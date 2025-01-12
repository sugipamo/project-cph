use std::os::unix::process::ExitStatusExt;
use std::process::ExitStatus;
use std::time::Duration;
use tokio::time;
use tokio::process::Child;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::fs::File;
use std::io::Read;
use anyhow::Context;

#[derive(Debug, Clone)]
pub struct ProcessStatus {
    pub exit_status: ExitStatus,
    pub memory_exceeded: bool,
}

#[derive(Debug, Clone)]
pub struct ProcessMonitor {
    memory_limit_mb: Option<u64>,
    child: Arc<Mutex<Child>>,
}

impl ProcessMonitor {
    pub fn new(memory_limit_mb: Option<u64>, child: Arc<Mutex<Child>>) -> Self {
        Self { memory_limit_mb, child }
    }

    async fn get_memory_usage_kb(&self) -> anyhow::Result<u64> {
        let child = self.child.lock().await;
        let pid = child.id().context("Failed to get process ID")?;
        let status_file = format!("/proc/{}/status", pid);
        let mut content = String::new();
        File::open(status_file)?.read_to_string(&mut content)?;

        // VmRSSとVmSwapの値を取得
        let vm_rss = Self::parse_memory_value(&content, "VmRSS:")?;
        let vm_swap = Self::parse_memory_value(&content, "VmSwap:").unwrap_or(0);

        Ok(vm_rss + vm_swap)
    }

    fn parse_memory_value(content: &str, prefix: &str) -> anyhow::Result<u64> {
        let line = content.lines()
            .find(|line| line.starts_with(prefix))
            .context(format!("Failed to find {} in status file", prefix))?;
        
        let value = line.split_whitespace()
            .nth(1)
            .context(format!("Failed to parse {} value", prefix))?
            .parse::<u64>()?;
        
        Ok(value)
    }

    async fn check_memory_limit(&self) -> bool {
        if let Some(limit_mb) = self.memory_limit_mb {
            if let Ok(usage_kb) = self.get_memory_usage_kb().await {
                return usage_kb > limit_mb * 1024;
            }
        }
        false
    }

    pub async fn wait_with_timeout<F, Fut>(&self, timeout: Duration, kill_fn: F) -> ProcessStatus
    where
        F: FnOnce() -> Fut + Clone,
        Fut: std::future::Future<Output = anyhow::Result<()>>,
    {
        let memory_check = async {
            while !self.check_memory_limit().await {
                time::sleep(Duration::from_millis(100)).await;
            }
        };

        let kill_fn2 = kill_fn.clone();
        let result = tokio::select! {
            result = self.wait() => result,
            _ = memory_check => {
                let _ = kill_fn().await;
                Ok(ExitStatus::from_raw(137)) // OOM killer signal
            }
        };

        match time::timeout(timeout, async { result }).await {
            Ok(Ok(status)) => ProcessStatus {
                exit_status: status,
                memory_exceeded: status.code() == Some(137),
            },
            Ok(Err(_)) => ProcessStatus {
                exit_status: ExitStatus::from_raw(1),
                memory_exceeded: false,
            },
            Err(_) => {
                let _ = kill_fn2().await;
                ProcessStatus {
                    exit_status: ExitStatus::from_raw(124),
                    memory_exceeded: false,
                }
            }
        }
    }

    async fn wait(&self) -> anyhow::Result<ExitStatus> {
        let mut child = self.child.lock().await;
        Ok(child.wait().await?.into())
    }
} 