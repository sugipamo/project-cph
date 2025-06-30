use crate::infrastructure::test_support::{Expectation, Mock};
use anyhow::Result;
use std::collections::HashMap;

#[derive(Default)]
pub struct MockShell {
    responses: HashMap<String, CommandResponse>,
    command_history: Vec<String>,
    expectations: Vec<Expectation>,
}

#[derive(Clone, Debug)]
pub struct CommandResponse {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
}

impl CommandResponse {
    pub fn success(stdout: impl Into<String>) -> Self {
        Self {
            stdout: stdout.into(),
            stderr: String::new(),
            exit_code: 0,
        }
    }

    pub fn failure(stderr: impl Into<String>, exit_code: i32) -> Self {
        Self {
            stdout: String::new(),
            stderr: stderr.into(),
            exit_code,
        }
    }
}

impl MockShell {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_response(mut self, command: impl Into<String>, response: CommandResponse) -> Self {
        self.responses.insert(command.into(), response);
        self
    }

    pub async fn execute(&mut self, command: &str) -> Result<CommandResponse> {
        if let Some(expectation) = self.expectations.first() {
            expectation.call();
        }

        self.command_history.push(command.to_string());

        self.responses
            .get(command)
            .cloned()
            .ok_or_else(|| anyhow::anyhow!("No response configured for command: {}", command))
    }

    pub fn get_history(&self) -> &[String] {
        &self.command_history
    }

    pub fn expect_command(&mut self) -> &mut Expectation {
        let expectation = Expectation::new();
        self.expectations.push(expectation);
        self.expectations.last_mut().unwrap()
    }
}

impl Mock<()> for MockShell {
    fn expect(&mut self) -> &mut Expectation {
        self.expect_command()
    }

    fn checkpoint(&mut self) {
        self.expectations.clear();
        self.command_history.clear();
    }

    fn verify(&self) -> Result<()> {
        for expectation in &self.expectations {
            expectation.verify()?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_mock_shell_success() -> Result<()> {
        let mut shell = MockShell::new()
            .with_response("echo hello", CommandResponse::success("hello\n"));

        let response = shell.execute("echo hello").await?;
        assert_eq!(response.stdout, "hello\n");
        assert_eq!(response.exit_code, 0);
        assert!(response.stderr.is_empty());

        Ok(())
    }

    #[tokio::test]
    async fn test_mock_shell_failure() -> Result<()> {
        let mut shell = MockShell::new()
            .with_response("false", CommandResponse::failure("Command failed", 1));

        let response = shell.execute("false").await?;
        assert_eq!(response.stderr, "Command failed");
        assert_eq!(response.exit_code, 1);
        assert!(response.stdout.is_empty());

        Ok(())
    }

    #[tokio::test]
    async fn test_mock_shell_history() -> Result<()> {
        let mut shell = MockShell::new()
            .with_response("echo one", CommandResponse::success("one\n"))
            .with_response("echo two", CommandResponse::success("two\n"));

        shell.execute("echo one").await?;
        shell.execute("echo two").await?;

        let history = shell.get_history();
        assert_eq!(history.len(), 2);
        assert_eq!(history[0], "echo one");
        assert_eq!(history[1], "echo two");

        Ok(())
    }

    #[tokio::test]
    async fn test_mock_shell_expectations() -> Result<()> {
        let mut shell = MockShell::new()
            .with_response("test", CommandResponse::success("ok"));

        shell.expect_command().times(1);

        shell.execute("test").await?;
        
        shell.verify()?;
        Ok(())
    }
}