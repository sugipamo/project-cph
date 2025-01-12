#[cfg(test)]
mod tests {
    use cph::process::{
        executor::ProcessExecutor,
        io::Buffer,
    };
    use std::{sync::Arc, time::Duration};
    use tokio::process::Command;
    use uuid::Uuid;

    #[tokio::test]
    async fn test_basic_process_execution() -> anyhow::Result<()> {
        let mut executor = ProcessExecutor::new();
        let mut command = Command::new("python3");
        command.args(&["-c", "print(1 + 2)"]);
        
        let buffer = Arc::new(Buffer::new(1024 * 1024)); // 1MB buffer
        let id = Uuid::new_v4().to_string();
        let mut process = executor.spawn(id, command, buffer, Some(32)).await?;
        let status = process.wait_with_timeout(Duration::from_secs(1)).await?;
        
        assert!(!status.memory_exceeded);
        assert!(status.exit_status.success());
        
        Ok(())
    }

    #[tokio::test]
    async fn test_timeout() -> anyhow::Result<()> {
        let mut executor = ProcessExecutor::new();
        let mut command = Command::new("python3");
        command.args(&["-c", "while True: pass"]);
        
        let buffer = Arc::new(Buffer::new(1024 * 1024)); // 1MB buffer
        let id = Uuid::new_v4().to_string();
        let mut process = executor.spawn(id, command, buffer, Some(32)).await?;
        let status = process.wait_with_timeout(Duration::from_secs(1)).await?;
        
        assert!(!status.memory_exceeded);
        assert!(!status.exit_status.success());
        
        Ok(())
    }

    #[tokio::test]
    async fn test_memory_limit() -> anyhow::Result<()> {
        let mut executor = ProcessExecutor::new();
        let mut command = Command::new("python3");
        command.args(&["-c", "x = [0] * 1000000000"]);
        
        let buffer = Arc::new(Buffer::new(1024 * 1024)); // 1MB buffer
        let id = Uuid::new_v4().to_string();
        let mut process = executor.spawn(id, command, buffer, Some(32)).await?;
        let status = process.wait_with_timeout(Duration::from_secs(1)).await?;
        
        assert!(status.memory_exceeded);
        assert!(!status.exit_status.success());
        
        Ok(())
    }
} 