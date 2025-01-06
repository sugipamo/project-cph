use async_trait::async_trait;
use std::process::Command;
use crate::docker::error::{DockerError, DockerResult};
use crate::docker::executor::{DockerCommand, DockerCommandExecutor, CommandOutput};

pub struct DefaultDockerCommandExecutor;

impl DefaultDockerCommandExecutor {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait]
impl DockerCommandExecutor for DefaultDockerCommandExecutor {
    async fn execute(&self, command: DockerCommand) -> DockerResult<CommandOutput> {
        let output = Command::new("docker")
            .args(&command.get_args())
            .output()
            .map_err(|e| DockerError::Container(format!("Dockerコマンドの実行に失敗しました: {}", e)))?;

        Ok(CommandOutput::new(
            output.status.success(),
            String::from_utf8_lossy(&output.stdout).to_string(),
            String::from_utf8_lossy(&output.stderr).to_string(),
        ))
    }
} 