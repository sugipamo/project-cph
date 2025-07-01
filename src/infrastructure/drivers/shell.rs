use crate::interfaces::shell::{Shell, CommandOutput};
use anyhow::Result;
use std::path::Path;
use std::process::Stdio;
use tokio::process::Command;
use tokio::io::AsyncWriteExt;

pub struct SystemShell;

impl SystemShell {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait::async_trait]
impl Shell for SystemShell {
    async fn execute(&self, command: &str) -> Result<CommandOutput> {
        self.execute_with_cwd(command, None).await
    }

    async fn execute_with_cwd(&self, command: &str, cwd: Option<&Path>) -> Result<CommandOutput> {
        self.execute_with_env(command, cwd, &[]).await
    }

    async fn execute_with_env(
        &self,
        command: &str,
        cwd: Option<&Path>,
        env: &[(String, String)],
    ) -> Result<CommandOutput> {
        let mut process = Command::new("sh");
        process.arg("-c").arg(command);

        if let Some(cwd) = cwd {
            process.current_dir(cwd);
        }

        for (key, value) in env {
            process.env(key, value);
        }

        let output = process.output().await?;

        Ok(CommandOutput {
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
            exit_code: output.status.code().unwrap_or(-1),
            status: output.status,
        })
    }

    async fn execute_with_input(&self, command: &str, input: &str) -> Result<CommandOutput> {
        let mut process = Command::new("sh");
        process.arg("-c")
            .arg(command)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        let mut child = process.spawn()?;
        
        if let Some(mut stdin) = child.stdin.take() {
            stdin.write_all(input.as_bytes()).await?;
            stdin.shutdown().await?;
        }
        
        let output = child.wait_with_output().await?;

        Ok(CommandOutput {
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
            exit_code: output.status.code().unwrap_or(-1),
            status: output.status,
        })
    }
    
    async fn execute_with_input_and_cwd(&self, command: &str, input: &str, cwd: Option<&Path>) -> Result<CommandOutput> {
        let mut process = Command::new("sh");
        process.arg("-c")
            .arg(command)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        if let Some(cwd_path) = cwd {
            process.current_dir(cwd_path);
        }

        let mut child = process.spawn()?;
        
        if let Some(mut stdin) = child.stdin.take() {
            stdin.write_all(input.as_bytes()).await?;
            stdin.shutdown().await?;
        }
        
        let output = child.wait_with_output().await?;

        Ok(CommandOutput {
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
            exit_code: output.status.code().unwrap_or(-1),
            status: output.status,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_system_shell_execute_simple_command() {
        let shell = SystemShell::new();
        let result = shell.execute("echo 'Hello, World!'").await.unwrap();
        
        assert_eq!(result.exit_code, 0);
        assert_eq!(result.stdout.trim(), "Hello, World!");
        assert_eq!(result.stderr, "");
    }

    #[tokio::test]
    async fn test_system_shell_execute_with_cwd() {
        let shell = SystemShell::new();
        let temp_dir = tempfile::TempDir::new().unwrap();
        let result = shell.execute_with_cwd("pwd", Some(temp_dir.path())).await.unwrap();
        
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
        let result = shell.execute("exit 1").await.unwrap();
        
        assert_eq!(result.exit_code, 1);
    }

    #[tokio::test]
    async fn test_system_shell_execute_stderr_output() {
        let shell = SystemShell::new();
        let result = shell.execute("echo 'error' >&2").await.unwrap();
        
        assert_eq!(result.exit_code, 0);
        assert_eq!(result.stdout, "");
        assert_eq!(result.stderr.trim(), "error");
    }
}