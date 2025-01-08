pub mod command;
pub mod compilation;
pub mod container;

pub use compilation::Compiler;
pub use container::Runtime;

use anyhow::Result;

#[derive(Debug)]
pub struct CommandOutput {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
}

impl CommandOutput {
    #[must_use = "この関数は新しいCommandOutputインスタンスを返します"]
    pub const fn new(stdout: String, stderr: String, exit_code: i32) -> Self {
        Self {
            stdout,
            stderr,
            exit_code,
        }
    }
}

#[async_trait::async_trait]
pub trait Executor {
    async fn execute(&self, command: command::Executor) -> Result<CommandOutput>;
} 