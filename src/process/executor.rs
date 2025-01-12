use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;
use tokio::process::{Child, Command};
use tokio::sync::Mutex;
use anyhow::{Result, bail};
use crate::process::io::Buffer;
use crate::process::monitor::{ProcessMonitor, ProcessStatus};

#[derive(Debug, Clone)]
pub struct Process {
    child: Arc<Mutex<Child>>,
    #[allow(dead_code)]
    buffer: Arc<Buffer>,
    monitor: ProcessMonitor,
}

impl Process {
    pub fn new(child: Child, buffer: Arc<Buffer>, memory_limit_mb: Option<u64>) -> Self {
        let child = Arc::new(Mutex::new(child));
        let monitor = ProcessMonitor::new(memory_limit_mb, child.clone());
        Self { child, buffer, monitor }
    }

    pub async fn kill(&mut self) -> Result<()> {
        let mut child = self.child.lock().await;
        child.kill().await?;
        Ok(())
    }

    pub async fn wait_with_timeout(&mut self, timeout: Duration) -> Result<ProcessStatus> {
        let mut this = self.clone();
        let kill_fn = move || async move { this.kill().await };
        Ok(self.monitor.wait_with_timeout(timeout, kill_fn).await)
    }

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

#[derive(Debug)]
pub struct ProcessExecutor {
    processes: Arc<Mutex<HashMap<String, Process>>>,
}

impl ProcessExecutor {
    pub fn new() -> Self {
        Self {
            processes: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub async fn spawn(&mut self, id: String, mut command: Command, buffer: Arc<Buffer>, memory_limit_mb: Option<u64>) -> Result<Process> {
        let child = command
            .kill_on_drop(true)
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .stdin(std::process::Stdio::piped())
            .spawn()?;

        let process = Process::new(child, buffer, memory_limit_mb);
        let mut processes = self.processes.lock().await;
        processes.insert(id, process.clone());
        Ok(process)
    }

    pub async fn kill(&mut self, id: &str) -> Result<()> {
        let mut processes = self.processes.lock().await;
        if let Some(mut process) = processes.remove(id) {
            process.kill().await?;
        }
        Ok(())
    }

    pub async fn write_stdin(&mut self, id: &str, input: &[u8]) -> Result<()> {
        let mut processes = self.processes.lock().await;
        if let Some(process) = processes.get_mut(id) {
            process.write_stdin(input).await
        } else {
            bail!("プロセスが見つかりません: {}", id)
        }
    }

    pub async fn wait_with_timeout(&mut self, id: &str, timeout: Duration) -> Result<ProcessStatus> {
        if let Some(process) = self.processes.lock().await.get_mut(id) {
            let status = process.wait_with_timeout(timeout).await?;
            Ok(status)
        } else {
            bail!("プロセスが見つかりません: {}", id)
        }
    }
} 