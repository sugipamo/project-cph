use std::time::Duration;
use tokio::time::timeout;
use anyhow::{Result, bail};
use crate::process::limits::MemoryMonitor;
use tokio::process::Child;

#[derive(Debug)]
pub struct ProcessStatus {
    pub exit_status: Option<std::process::ExitStatus>,
    pub memory_exceeded: bool,
}

pub struct ProcessMonitor {
    memory_monitor: Option<MemoryMonitor>,
}

impl ProcessMonitor {
    pub fn new(memory_monitor: Option<MemoryMonitor>) -> Self {
        Self { memory_monitor }
    }

    pub async fn check_status(&self) -> Result<ProcessStatus> {
        // メモリ使用量をチェック
        if let Some(monitor) = &self.memory_monitor {
            if monitor.is_exceeded()
                .context("メモリ使用量の確認に失敗しました")? {
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

    pub async fn wait_with_timeout(
        &self,
        child: &mut Child,
        timeout_secs: u64,
        kill_fn: impl Fn() -> Result<()>,
    ) -> Result<ProcessStatus> {
        let timeout_duration = Duration::from_secs(timeout_secs);
        
        let wait_future = async {
            let mut interval = tokio::time::interval(Duration::from_millis(100));
            loop {
                interval.tick().await;
                
                // メモリ使用量をチェック
                let status = self.check_status().await?;
                if status.memory_exceeded {
                    kill_fn()?;
                    return Ok(status);
                }

                // プロセスの終了を確認
                if let Ok(Some(status)) = child.try_wait() {
                    return Ok(ProcessStatus {
                        exit_status: Some(status),
                        memory_exceeded: false,
                    });
                }
            }
        };

        match timeout(timeout_duration, wait_future).await {
            Ok(result) => result,
            Err(_) => {
                kill_fn()?;
                bail!("プロセスがタイムアウトしました（{}秒）", timeout_secs)
            }
        }
    }
} 