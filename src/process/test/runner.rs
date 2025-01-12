use std::sync::Arc;
use tokio::process::Command;
use anyhow::Result;
use uuid::Uuid;
use crate::process::executor::ProcessExecutor;
use crate::process::io::Buffer;
use std::time::Duration;

pub struct TestRunner {
    executor: ProcessExecutor,
}

impl TestRunner {
    pub fn new() -> Self {
        Self {
            executor: ProcessExecutor::new(),
        }
    }

    pub async fn run_test(&mut self, source_file: &str, input: &str, timeout_secs: u64, memory_limit_mb: Option<u64>) -> Result<String> {
        let id = Uuid::new_v4().to_string();
        let buffer = Arc::new(Buffer::new(1024 * 1024)); // 1MB

        let mut command = Command::new(source_file);
        command.kill_on_drop(true);
        command.stdin(std::process::Stdio::piped());
        command.stdout(std::process::Stdio::piped());
        command.stderr(std::process::Stdio::piped());

        self.executor.spawn(id.clone(), command, buffer.clone(), memory_limit_mb).await?;
        self.executor.write_stdin(&id, input.as_bytes()).await?;
        let status = self.executor.wait_with_timeout(&id, Duration::from_secs(timeout_secs)).await?;
        assert!(!status.exit_status.success(), "プロセスはタイムアウトで終了するはずです");

        let output = buffer.get_contents().await?;
        Ok(String::from_utf8_lossy(&output).to_string())
    }
} 