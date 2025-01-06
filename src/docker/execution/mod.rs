pub mod command;
pub mod container;
pub mod compilation;

pub use command::DefaultDockerCommandExecutor;
pub use container::DefaultContainerManager;
pub use compilation::DefaultCompilationManager;

// 共通のトレイトと型定義
use async_trait::async_trait;
use crate::docker::error::DockerResult;

#[derive(Debug)]
pub struct CommandOutput {
    pub success: bool,
    pub stdout: String,
    pub stderr: String,
}

impl CommandOutput {
    pub fn new(success: bool, stdout: String, stderr: String) -> Self {
        Self {
            success,
            stdout,
            stderr,
        }
    }
}

#[async_trait]
pub trait DockerCommandExecutor: Send + Sync {
    async fn execute(&self, command: DockerCommand) -> DockerResult<CommandOutput>;
}

#[derive(Debug)]
pub struct DockerCommand {
    args: Vec<String>,
}

impl DockerCommand {
    pub fn new(command: &str) -> Self {
        Self {
            args: vec![command.to_string()],
        }
    }

    pub fn arg(mut self, arg: &str) -> Self {
        self.args.push(arg.to_string());
        self
    }

    pub fn args(mut self, args: Vec<String>) -> Self {
        self.args.extend(args);
        self
    }

    pub fn env(mut self, key: &str, value: &str) -> Self {
        self.args.push("-e".to_string());
        self.args.push(format!("{}={}", key, value));
        self
    }

    pub fn get_args(&self) -> Vec<String> {
        self.args.clone()
    }
} 