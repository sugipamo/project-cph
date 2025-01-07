pub mod command;
pub mod compilation;
pub mod container;

pub use command::DockerCommand;
pub use compilation::CompilationManager;
pub use container::DockerContainer;

use crate::error::Result;
use std::process::Output;

pub struct CommandOutput {
    pub stdout: String,
    pub stderr: String,
    pub status: i32,
}

impl From<Output> for CommandOutput {
    fn from(output: Output) -> Self {
        Self {
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
            status: output.status.code().unwrap_or(-1),
        }
    }
}

#[async_trait::async_trait]
pub trait Executor {
    async fn execute(&self, command: DockerCommand) -> Result<CommandOutput>;
} 