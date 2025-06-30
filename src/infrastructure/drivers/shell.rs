use crate::interfaces::shell::{Shell, CommandOutput};
use anyhow::Result;
use std::path::Path;
use tokio::process::Command;

pub struct SystemShell;

impl SystemShell {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait::async_trait]
impl Shell for SystemShell {
    async fn execute(&self, command: &str, cwd: Option<&Path>) -> Result<CommandOutput> {
        self.execute_with_env(command, cwd, &[]).await
    }

    async fn execute_with_env(
        &self,
        command: &str,
        cwd: Option<&Path>,
        env: &[(String, String)],
    ) -> Result<CommandOutput> {
        let mut cmd = Command::new("sh");
        cmd.arg("-c").arg(command);

        if let Some(cwd) = cwd {
            cmd.current_dir(cwd);
        }

        for (key, value) in env {
            cmd.env(key, value);
        }

        let output = cmd.output().await?;

        Ok(CommandOutput {
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
            exit_code: output.status.code().unwrap_or(-1),
        })
    }
}