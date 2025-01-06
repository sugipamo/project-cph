use std::process::Command;
use async_trait::async_trait;
use crate::docker::error::{DockerError, DockerResult};
use crate::docker::traits::DockerCommandExecutor;

pub struct DockerCommandLayer {
    executor: Box<dyn DockerCommandExecutor>,
}

impl DockerCommandLayer {
    pub fn new(executor: Box<dyn DockerCommandExecutor>) -> Self {
        Self { executor }
    }

    pub async fn run_command(&self, args: Vec<String>) -> DockerResult<(String, String)> {
        let (success, stdout, stderr) = self.executor.execute_command(args).await?;
        if success {
            Ok((stdout, stderr))
        } else {
            Err(DockerError::Command(format!(
                "Dockerコマンドの実行に失敗しました: {}",
                stderr
            )))
        }
    }

    pub async fn run_container_command(
        &self,
        container_id: &str,
        command: &str,
    ) -> DockerResult<(String, String)> {
        let args = vec![
            "exec".to_string(),
            "-i".to_string(),
            container_id.to_string(),
            "sh".to_string(),
            "-c".to_string(),
            command.to_string(),
        ];
        self.run_command(args).await
    }
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