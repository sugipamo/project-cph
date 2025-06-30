use anyhow::Result;
use std::path::Path;

pub struct CommandOutput {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
}

#[async_trait::async_trait]
pub trait Shell: Send + Sync {
    async fn execute(&self, command: &str, cwd: Option<&Path>) -> Result<CommandOutput>;
    async fn execute_with_env(
        &self,
        command: &str,
        cwd: Option<&Path>,
        env: &[(String, String)],
    ) -> Result<CommandOutput>;
}