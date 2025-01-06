use async_trait::async_trait;
use std::process::Command;
use crate::docker::error::{DockerError, DockerResult};

#[async_trait]
pub trait DockerCommandExecutor: Send + Sync {
    async fn execute_command(&self, args: Vec<String>) -> DockerResult<(bool, String, String)>;
}

pub struct DefaultDockerExecutor;

impl DefaultDockerExecutor {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait]
impl DockerCommandExecutor for DefaultDockerExecutor {
    async fn execute_command(&self, args: Vec<String>) -> DockerResult<(bool, String, String)> {
        let mut command = Command::new("docker");
        command.args(&args);

        let output = command
            .output()
            .map_err(|e| DockerError::Command(format!("コマンドの実行に失敗しました: {}", e)))?;

        Ok((
            output.status.success(),
            String::from_utf8_lossy(&output.stdout).to_string(),
            String::from_utf8_lossy(&output.stderr).to_string(),
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use mockall::mock;

    mock! {
        pub DockerExecutor {}
        #[async_trait]
        impl DockerCommandExecutor for DockerExecutor {
            async fn execute_command(&self, args: Vec<String>) -> DockerResult<(bool, String, String)>;
        }
    }
} 