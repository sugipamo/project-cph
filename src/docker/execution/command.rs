use async_trait::async_trait;
use tokio::process::Command;
use crate::docker::error::{DockerError, DockerResult};
use super::{DockerCommand, DockerCommandExecutor, CommandOutput};

pub struct DefaultDockerCommandExecutor;

impl DefaultDockerCommandExecutor {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait]
impl DockerCommandExecutor for DefaultDockerCommandExecutor {
    async fn execute(&self, command: DockerCommand) -> DockerResult<CommandOutput> {
        let mut cmd = Command::new("docker");
        cmd.args(command.get_args());

        let output = cmd.output().await.map_err(|e| {
            DockerError::Command(format!("Dockerコマンドの実行に失敗しました: {}", e))
        })?;

        Ok(CommandOutput::new(
            output.status.success(),
            String::from_utf8_lossy(&output.stdout).to_string(),
            String::from_utf8_lossy(&output.stderr).to_string(),
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_docker_command_executor() {
        let executor = DefaultDockerCommandExecutor::new();
        let command = DockerCommand::new("version");
        
        let result = executor.execute(command).await;
        assert!(result.is_ok());
        
        let output = result.unwrap();
        assert!(output.success);
        assert!(!output.stdout.is_empty());
    }
} 