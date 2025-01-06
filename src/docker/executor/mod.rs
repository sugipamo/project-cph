use async_trait::async_trait;
use std::process::Command;
use std::collections::HashMap;
use crate::docker::error::{DockerError, DockerResult};

#[derive(Debug, Clone)]
pub struct DockerCommand {
    pub command: String,
    pub args: Vec<String>,
    pub env: Option<HashMap<String, String>>,
}

impl DockerCommand {
    pub fn new(command: impl Into<String>) -> Self {
        Self {
            command: command.into(),
            args: Vec::new(),
            env: None,
        }
    }

    pub fn arg(mut self, arg: impl Into<String>) -> Self {
        self.args.push(arg.into());
        self
    }

    pub fn args(mut self, args: impl IntoIterator<Item = impl Into<String>>) -> Self {
        self.args.extend(args.into_iter().map(Into::into));
        self
    }

    pub fn env(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        let env = self.env.get_or_insert_with(HashMap::new);
        env.insert(key.into(), value.into());
        self
    }
}

#[derive(Debug, Clone)]
pub struct CommandOutput {
    pub success: bool,
    pub stdout: String,
    pub stderr: String,
}

#[async_trait]
pub trait DockerCommandExecutor: Send + Sync {
    async fn execute(&self, command: DockerCommand) -> DockerResult<CommandOutput>;
}

pub struct DefaultDockerExecutor;

impl DefaultDockerExecutor {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait]
impl DockerCommandExecutor for DefaultDockerExecutor {
    async fn execute(&self, command: DockerCommand) -> DockerResult<CommandOutput> {
        let mut cmd = Command::new("docker");
        
        // コマンドと引数を設定
        cmd.arg(&command.command);
        cmd.args(&command.args);

        // 環境変数を設定
        if let Some(env) = command.env {
            for (key, value) in env {
                cmd.env(key, value);
            }
        }

        let output = cmd
            .output()
            .map_err(|e| DockerError::Command(format!("コマンドの実行に失敗しました: {}", e)))?;

        Ok(CommandOutput {
            success: output.status.success(),
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        })
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
            async fn execute(&self, command: DockerCommand) -> DockerResult<CommandOutput>;
        }
    }

    #[tokio::test]
    async fn test_docker_command_builder() {
        let command = DockerCommand::new("run")
            .arg("-d")
            .args(vec!["--name", "test-container"])
            .env("MEMORY_LIMIT", "512m");

        assert_eq!(command.command, "run");
        assert_eq!(command.args, vec!["-d", "--name", "test-container"]);
        assert_eq!(
            command.env.unwrap().get("MEMORY_LIMIT").unwrap(),
            "512m"
        );
    }

    #[tokio::test]
    async fn test_docker_executor() {
        let executor = DefaultDockerExecutor::new();
        let command = DockerCommand::new("version");

        let result = executor.execute(command).await;
        assert!(result.is_ok());
    }
} 