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
        let mut cmd = Command::new(&command.command);
        cmd.args(&command.args);

        if let Some(env) = command.env {
            for (key, value) in env {
                cmd.env(key, value);
            }
        }

        let output = cmd.output().map_err(|e| DockerError::Command(e.to_string()))?;

        Ok(CommandOutput {
            success: output.status.success(),
            stdout: String::from_utf8_lossy(&output.stdout).into_owned(),
            stderr: String::from_utf8_lossy(&output.stderr).into_owned(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_docker_command_builder() {
        let command = DockerCommand::new("docker")
            .arg("run")
            .args(vec!["--rm", "-it"])
            .env("TEST", "value");

        assert_eq!(command.command, "docker");
        assert_eq!(command.args, vec!["run", "--rm", "-it"]);
        assert_eq!(command.env.unwrap().get("TEST").unwrap(), "value");
    }

    #[tokio::test]
    async fn test_docker_executor() {
        let executor = DefaultDockerExecutor::new();
        let command = DockerCommand::new("echo").arg("test");

        let output = executor.execute(command).await.unwrap();
        assert!(output.success);
        assert_eq!(output.stdout.trim(), "test");
        assert!(output.stderr.is_empty());
    }
} 