mod command;
mod container;
mod compilation;

pub use command::DockerCommand;
pub use container::ContainerManager;
pub use compilation::CompilationManager;

// 共通のトレイトと型定義
use async_trait::async_trait;
use crate::error::Result;

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
    async fn execute(&self, command: DockerCommand) -> Result<CommandOutput>;
} 