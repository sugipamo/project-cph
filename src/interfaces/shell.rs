use anyhow::Result;
use std::path::Path;
use std::process::ExitStatus;

pub struct CommandOutput {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
    pub status: ExitStatus,
}

#[async_trait::async_trait]
pub trait Shell: Send + Sync {
    async fn execute(&self, command: &str) -> Result<CommandOutput>;
    async fn execute_with_cwd(&self, command: &str, cwd: Option<&Path>) -> Result<CommandOutput>;
    async fn execute_with_env(
        &self,
        command: &str,
        cwd: Option<&Path>,
        env: &[(String, String)],
    ) -> Result<CommandOutput>;
    async fn execute_with_input(&self, command: &str, input: &str) -> Result<CommandOutput>;
    async fn execute_with_input_and_cwd(&self, command: &str, input: &str, cwd: Option<&Path>) -> Result<CommandOutput>;
}