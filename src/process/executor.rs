use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Mutex;
use tokio::process::{Child, Command};
use tokio::io::{BufReader, AsyncBufReadExt, AsyncWriteExt};
use tokio::time::timeout;
use anyhow::{Result, Context};
use crate::config::Config;
use uuid::Uuid;
use bytes::Bytes;
use crate::process::io::Buffer;
use crate::process::limits::{ProcessLimits, MemoryMonitor};

#[derive(Debug)]
pub struct Process {
    pub id: String,
    pub child: Child,
    pub config: ProcessConfig,
    pub memory_monitor: Option<MemoryMonitor>,
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
    buffer: Arc<Buffer>,
    config: Config,
}

#[derive(Debug)]
pub struct ProcessStatus {
    pub exit_status: Option<std::process::ExitStatus>,
    pub memory_exceeded: bool,
}

impl ProcessExecutor {
    pub fn new(config: Config) -> Self {
        Self {
            processes: Arc::new(Mutex::new(HashMap::new())),
            buffer: Arc::new(Buffer::new()),
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

        // 環境変数の設定
        if let Ok(env_vars) = language_config.get::<Vec<String>>("env_vars") {
            for env_var in env_vars {
                if let Some((key, value)) = env_var.split_once('=') {
                    command.env(key, value);
                }
            }
        }

        for (key, value) in &config.env_vars {
            command.env(key, value);
        }

        let mut child = command.spawn()
            .context("プロセスの起動に失敗しました")?;
        
        let id = Uuid::new_v4().to_string();

        // メモリ監視の設定
        let memory_monitor = if let Some(pid) = child.id() {
            Some(MemoryMonitor::new(pid, memory_limit_mb))
        } else {
            None
        };

        // 標準出力の非同期処理を設定
        if let Some(stdout) = child.stdout.take() {
            let buffer = self.buffer.clone();
            let process_id = id.clone();
            tokio::spawn(async move {
                let mut reader = BufReader::new(stdout);
                let mut line = String::new();
                while let Ok(n) = reader.read_line(&mut line).await {
                    if n == 0 { break; }
                    if let Err(e) = buffer.append(&process_id, Bytes::from(line.clone())).await {
                        eprintln!("stdout バッファリングエラー: {}", e);
                    }
                    line.clear();
                }
            });
        }

        // 標準エラー出力の非同期処理を設定
        if let Some(stderr) = child.stderr.take() {
            let buffer = self.buffer.clone();
            let process_id = id.clone();
            tokio::spawn(async move {
                let mut reader = BufReader::new(stderr);
                let mut line = String::new();
                while let Ok(n) = reader.read_line(&mut line).await {
                    if n == 0 { break; }
                    if let Err(e) = buffer.append(&process_id, Bytes::from(line.clone())).await {
                        eprintln!("stderr バッファリングエラー: {}", e);
                    }
                    line.clear();
                }
            });
        }

        let process = Process {
            id: id.clone(),
            child,
            config,
            memory_monitor,
        };

        self.processes.lock().await.insert(id.clone(), process);
        Ok(id)
    }

    /// プロセスの状態を確認します
    async fn check_process_status(&self, id: &str) -> Result<ProcessStatus> {
        let processes = self.processes.lock().await;
        let process = processes.get(id)
            .ok_or_else(|| anyhow::anyhow!("指定されたIDのプロセスが見つかりません: {}", id))?;

        // メモリ使用量をチェック
        if let Some(monitor) = &process.memory_monitor {
            if monitor.is_exceeded()? {
                return Ok(ProcessStatus {
                    exit_status: None,
                    memory_exceeded: true,
                });
            }
        }

        Ok(ProcessStatus {
            exit_status: None,
            memory_exceeded: false,
        })
    }

    /// タイムアウト付きでプロセスの終了を待ちます
    pub async fn wait_with_timeout(&self, id: &str, timeout_secs: u64) -> Result<ProcessStatus> {
        let timeout_duration = Duration::from_secs(timeout_secs);
        
        let wait_future = async {
            let mut interval = tokio::time::interval(Duration::from_millis(100));
            loop {
                interval.tick().await;
                
                // プロセスの状態をチェック
                let status = self.check_process_status(id).await?;
                if status.memory_exceeded {
                    self.kill(id).await?;
                    return Ok(status);
                }

                // プロセスの終了を確認
                if let Some(process) = self.processes.lock().await.get_mut(id) {
                    if let Ok(exit_status) = process.child.try_wait()? {
                        if let Some(status) = exit_status {
                            return Ok(ProcessStatus {
                                exit_status: Some(status),
                                memory_exceeded: false,
                            });
                        }
                    }
                }
            }
        };

        match timeout(timeout_duration, wait_future).await {
            Ok(result) => result,
            Err(_) => {
                self.kill(id).await?;
                anyhow::bail!("プロセスがタイムアウトしました（{}秒）", timeout_secs)
            }
        }
    }

    /// プロセスに入力を送信します
    pub async fn write_stdin(&self, id: &str, input: &str) -> Result<()> {
        let mut processes = self.processes.lock().await;
        if let Some(process) = processes.get_mut(id) {
            if let Some(stdin) = process.child.stdin.as_mut() {
                stdin.write_all(input.as_bytes()).await
                    .context("標準入力の書き込みに失敗しました")?;
                stdin.flush().await
                    .context("標準入力のフラッシュに失敗しました")?;
                Ok(())
            } else {
                anyhow::bail!("プロセスの標準入力が利用できません")
            }
        } else {
            anyhow::bail!("指定されたIDのプロセスが見つかりません: {}", id)
        }
    }

    /// プロセスの出力を取得します
    pub async fn read_output(&self, id: &str) -> Option<Vec<Bytes>> {
        self.buffer.get(id).await
    }

    pub async fn kill(&self, id: &str) -> Result<()> {
        if let Some(process) = self.processes.lock().await.get_mut(id) {
            process.child.kill().await
                .context("プロセスの強制終了に失敗しました")?;
        }
        Ok(())
    }
} 