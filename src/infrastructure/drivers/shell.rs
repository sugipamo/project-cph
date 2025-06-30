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

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_system_shell_execute_simple_command() {
        let shell = SystemShell::new();
        let result = shell.execute("echo 'Hello, World!'", None).await.unwrap();
        
        assert_eq!(result.exit_code, 0);
        assert_eq!(result.stdout.trim(), "Hello, World!");
        assert_eq!(result.stderr, "");
    }

    #[tokio::test]
    async fn test_system_shell_execute_with_cwd() {
        let shell = SystemShell::new();
        let temp_dir = tempfile::TempDir::new().unwrap();
        let result = shell.execute("pwd", Some(temp_dir.path())).await.unwrap();
        
        assert_eq!(result.exit_code, 0);
        assert_eq!(result.stdout.trim(), temp_dir.path().to_string_lossy());
    }

    #[tokio::test]
    async fn test_system_shell_execute_with_env() {
        let shell = SystemShell::new();
        let env = vec![("TEST_VAR".to_string(), "test_value".to_string())];
        let result = shell.execute_with_env("echo $TEST_VAR", None, &env).await.unwrap();
        
        assert_eq!(result.exit_code, 0);
        assert_eq!(result.stdout.trim(), "test_value");
    }

    #[tokio::test]
    async fn test_system_shell_execute_failed_command() {
        let shell = SystemShell::new();
        let result = shell.execute("exit 1", None).await.unwrap();
        
        assert_eq!(result.exit_code, 1);
    }

    #[tokio::test]
    async fn test_system_shell_execute_stderr_output() {
        let shell = SystemShell::new();
        let result = shell.execute("echo 'error' >&2", None).await.unwrap();
        
        assert_eq!(result.exit_code, 0);
        assert_eq!(result.stdout, "");
        assert_eq!(result.stderr.trim(), "error");
    }
}