use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::process::{Child, Command};
use anyhow::{Result, Context};
use crate::config::Config;
use uuid::Uuid;
use bytes::Bytes;
use crate::process::io::{Buffer, IoHandler};
use crate::process::limits::{ProcessLimits, MemoryMonitor};
use crate::process::monitor::{ProcessMonitor, ProcessStatus};
use std::path::PathBuf;

#[derive(Debug)]
pub struct Process {
    pub id: String,
    pub child: Child,
    pub config: ProcessConfig,
    pub monitor: ProcessMonitor,
    temp_files: Vec<PathBuf>,
}

impl Drop for Process {
    fn drop(&mut self) {
        // プロセスが実行中なら強制終了
        if let Ok(None) = self.child.try_wait() {
            let _ = self.child.start_kill();
        }

        // 一時ファイルの削除
        for path in &self.temp_files {
            if let Err(e) = std::fs::remove_file(path) {
                eprintln!("一時ファイルの削除に失敗しました: {} ({})", path.display(), e);
            }
        }
    }
}

#[derive(Clone, Debug)]
pub struct ProcessConfig {
    pub language: String,
    pub command: String,
    pub args: Vec<String>,
    pub env_vars: HashMap<String, String>,
    pub working_dir: Option<String>,
}

pub struct ProcessExecutor {
    processes: Arc<Mutex<HashMap<String, Process>>>,
    io_handler: IoHandler,
    config: Config,
}

impl Drop for ProcessExecutor {
    fn drop(&mut self) {
        // 非同期コンテキストでの終了処理をブロッキングで実行
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let mut processes = self.processes.lock().await;
            for (id, _) in processes.drain() {
                self.io_handler.cleanup(&id).await;
            }
        });
    }
}

impl ProcessExecutor {
    pub fn new(config: Config) -> Self {
        let buffer = Arc::new(Buffer::new());
        Self {
            processes: Arc::new(Mutex::new(HashMap::new())),
            io_handler: IoHandler::new(buffer),
            config,
        }
    }

    pub async fn spawn(&self, config: ProcessConfig) -> Result<String> {
        let language_config = self.config.get_section(&format!("languages.{}", config.language))
            .context("言語設定の取得に失敗しました")?;

        let timeout_seconds: u64 = language_config.get("timeout_seconds")
            .unwrap_or(10);
        let memory_limit_mb: u64 = language_config.get("memory_limit_mb")
            .unwrap_or(256);

        let mut command = Command::new(&config.command);
        command
            .args(&config.args)
            .stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .set_memory_limit(memory_limit_mb);

        if let Some(dir) = &config.working_dir {
            command.current_dir(dir);
        }

        self.setup_env_vars(&mut command, &language_config, &config)?;

        let mut child = command.spawn()
            .context("プロセスの起動に失敗しました")?;
        
        let id = Uuid::new_v4().to_string();

        // メモリ監視の設定
        let memory_monitor = if let Some(pid) = child.id() {
            Some(MemoryMonitor::new(pid, memory_limit_mb))
        } else {
            None
        };

        // I/O処理の設定
        self.io_handler.setup_io(&mut child, &id).await;

        let process = Process {
            id: id.clone(),
            child,
            config,
            monitor: ProcessMonitor::new(memory_monitor),
            temp_files: Vec::new(),
        };

        self.processes.lock().await.insert(id.clone(), process);
        Ok(id)
    }

    // 一時ファイルを追加
    pub async fn add_temp_file(&self, id: &str, path: PathBuf) -> Result<()> {
        let mut processes = self.processes.lock().await;
        let process = processes.get_mut(id)
            .context("指定されたIDのプロセスが見つかりません")?;
        process.temp_files.push(path);
        Ok(())
    }

    fn setup_env_vars(
        &self,
        command: &mut Command,
        language_config: &Config,
        process_config: &ProcessConfig,
    ) -> Result<()> {
        if let Ok(env_vars) = language_config.get::<Vec<String>>("env_vars") {
            for env_var in env_vars {
                if let Some((key, value)) = env_var.split_once('=') {
                    command.env(key, value);
                }
            }
        }

        for (key, value) in &process_config.env_vars {
            command.env(key, value);
        }

        Ok(())
    }

    pub async fn wait_with_timeout(&self, id: &str, timeout_secs: u64) -> Result<ProcessStatus> {
        let mut processes = self.processes.lock().await;
        let process = processes.get_mut(id)
            .context("指定されたIDのプロセスが見つかりません")?;

        let kill_fn = || self.kill(id);
        process.monitor.wait_with_timeout(&mut process.child, timeout_secs, kill_fn).await
    }

    pub async fn write_stdin(&self, id: &str, input: &str) -> Result<()> {
        let mut processes = self.processes.lock().await;
        let process = processes.get_mut(id)
            .context("指定されたIDのプロセスが見つかりません")?;

        IoHandler::write_stdin(&mut process.child, input).await
    }

    pub async fn read_output(&self, id: &str) -> Option<Vec<Bytes>> {
        self.io_handler.read_output(id).await
    }

    pub async fn kill(&self, id: &str) -> Result<()> {
        if let Some(process) = self.processes.lock().await.get_mut(id) {
            process.child.kill().await
                .context("プロセスの強制終了に失敗しました")?;
        }
        Ok(())
    }

    /// プロセスを終了し、関連リソースをクリーンアップします
    pub async fn cleanup(&self, id: &str) -> Result<()> {
        // プロセスを強制終了
        self.kill(id).await?;

        // I/Oバッファをクリーンアップ
        self.io_handler.cleanup(id).await;

        // プロセスをマップから削除（Dropトレイトが呼ばれ、一時ファイルが削除される）
        let mut processes = self.processes.lock().await;
        processes.remove(id);

        Ok(())
    }

    /// すべてのプロセスを終了し、リソースをクリーンアップします
    pub async fn cleanup_all(&self) -> Result<()> {
        let mut processes = self.processes.lock().await;
        let ids: Vec<String> = processes.keys().cloned().collect();
        drop(processes); // ロックを解放

        for id in ids {
            self.cleanup(&id).await?;
        }
        Ok(())
    }
} 