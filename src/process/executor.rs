use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;
use tokio::process::{Child, Command};
use tokio::sync::Mutex;
use anyhow::{Result, bail};
use crate::process::io::Buffer;
use crate::process::monitor::{Monitor, Status};

/// 単一のプロセスを表す構造体
#[derive(Debug, Clone)]
pub struct Process {
    child: Arc<Mutex<Child>>,
    #[allow(dead_code)]
    buffer: Arc<Buffer>,
    monitor: Monitor,
}

impl Process {
    /// 新しいプロセスを作成する
    /// 
    /// # Arguments
    /// 
    /// * `child` - 子プロセス
    /// * `buffer` - 入出力バッファ
    /// * `memory_limit_mb` - メモリ制限（MB単位）
    #[must_use]
    pub fn new(child: Child, buffer: Arc<Buffer>, memory_limit_mb: Option<u64>) -> Self {
        let child = Arc::new(Mutex::new(child));
        let monitor = Monitor::new(memory_limit_mb, child.clone());
        Self { child, buffer, monitor }
    }

    /// プロセスを強制終了する
    /// 
    /// # Errors
    /// 
    /// * プロセスの終了に失敗した場合
    pub async fn kill(&mut self) -> Result<()> {
        let mut child = self.child.lock().await;
        child.kill().await?;
        Ok(())
    }

    /// タイムアウト付きでプロセスの終了を待機する
    /// 
    /// # Arguments
    /// 
    /// * `timeout` - タイムアウト時間
    /// 
    /// # Errors
    /// 
    /// * プロセスの終了待機に失敗した場合
    /// * タイムアウトが発生した場合
    pub async fn wait_with_timeout(&mut self, timeout: Duration) -> Result<Status> {
        let mut this = self.clone();
        let kill_fn = move || async move { this.kill().await };
        Ok(self.monitor.wait_with_timeout(timeout, kill_fn).await)
    }

    /// プロセスの標準入力にデータを書き込む
    /// 
    /// # Arguments
    /// 
    /// * `input` - 書き込むデータ
    /// 
    /// # Errors
    /// 
    /// * 書き込みに失敗した場合
    pub async fn write_stdin(&mut self, input: &[u8]) -> Result<()> {
        let mut child = self.child.lock().await;
        if let Some(stdin) = child.stdin.as_mut() {
            use tokio::io::AsyncWriteExt;
            stdin.write_all(input).await?;
            stdin.flush().await?;
        }
        Ok(())
    }
}

/// プロセスの実行と管理を行う構造体
#[derive(Debug)]
pub struct Executor {
    processes: Arc<Mutex<HashMap<String, Process>>>,
}

#[allow(clippy::new_without_default)]
impl Executor {
    /// 新しいエグゼキューターを作成する
    #[must_use]
    pub fn new() -> Self {
        Self {
            processes: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// 新しいプロセスを生成する
    /// 
    /// # Arguments
    /// 
    /// * `id` - プロセスID
    /// * `command` - 実行するコマンド
    /// * `buffer` - 入出力バッファ
    /// * `memory_limit_mb` - メモリ制限（MB単位）
    /// 
    /// # Errors
    /// 
    /// * プロセスの生成に失敗した場合
    pub async fn spawn(&mut self, id: String, mut command: Command, buffer: Arc<Buffer>, memory_limit_mb: Option<u64>) -> Result<Process> {
        let child = command
            .kill_on_drop(true)
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .stdin(std::process::Stdio::piped())
            .spawn()?;

        let process = Process::new(child, buffer, memory_limit_mb);
        self.processes.lock().await.insert(id, process.clone());
        Ok(process)
    }

    /// プロセスを強制終了する
    /// 
    /// # Arguments
    /// 
    /// * `id` - プロセスID
    /// 
    /// # Errors
    /// 
    /// * プロセスの終了に失敗した場合
    pub async fn kill(&mut self, id: &str) -> Result<()> {
        if let Some(mut process) = self.processes.lock().await.remove(id) {
            process.kill().await?;
        }
        Ok(())
    }

    /// プロセスの標準入力にデータを書き込む
    /// 
    /// # Arguments
    /// 
    /// * `id` - プロセスID
    /// * `input` - 書き込むデータ
    /// 
    /// # Errors
    /// 
    /// * プロセスが見つからない場合
    /// * 書き込みに失敗した場合
    pub async fn write_stdin(&mut self, id: &str, input: &[u8]) -> Result<()> {
        let mut processes = self.processes.lock().await;
        if let Some(process) = processes.get_mut(id) {
            process.write_stdin(input).await
        } else {
            bail!("プロセスが見つかりません: {id}")
        }
    }

    /// タイムアウト付きでプロセスの終了を待機する
    /// 
    /// # Arguments
    /// 
    /// * `id` - プロセスID
    /// * `timeout` - タイムアウト時間
    /// 
    /// # Errors
    /// 
    /// * プロセスが見つからない場合
    /// * プロセスの終了待機に失敗した場合
    pub async fn wait_with_timeout(&mut self, id: &str, timeout: Duration) -> Result<Status> {
        let mut processes = self.processes.lock().await;
        if let Some(process) = processes.get_mut(id) {
            let status = process.wait_with_timeout(timeout).await?;
            Ok(status)
        } else {
            bail!("プロセスが見つかりません: {id}")
        }
    }
} 