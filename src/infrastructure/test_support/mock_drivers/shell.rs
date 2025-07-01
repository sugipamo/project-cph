use crate::infrastructure::test_support::{Expectation, Mock};
use crate::interfaces::shell::{Shell, CommandOutput};
use anyhow::Result;
use std::collections::HashMap;
use std::path::Path;
use std::process::ExitStatus;
use std::sync::{Arc, Mutex};

#[derive(Clone)]
pub struct MockShell {
    inner: Arc<Mutex<MockShellInner>>,
}

#[derive(Default)]
struct MockShellInner {
    responses: HashMap<String, CommandResponse>,
    context_responses: HashMap<CommandContext, CommandResponse>,
    command_history: Vec<CommandRecord>,
    expectations: Vec<Expectation>,
}

#[derive(Clone, Debug, Hash, Eq, PartialEq)]
pub struct CommandContext {
    pub command: String,
    pub input: Option<String>,
    pub cwd: Option<String>,
}

#[derive(Clone, Debug)]
pub struct CommandRecord {
    pub command: String,
    pub input: Option<String>,
    pub cwd: Option<String>,
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

impl Default for MockShell {
    fn default() -> Self {
        Self {
            inner: Arc::new(Mutex::new(MockShellInner::default())),
        }
    }
}

impl MockShell {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_response(self, command: impl Into<String>, response: CommandResponse) -> Self {
        self.inner.lock().unwrap().responses.insert(command.into(), response);
        self
    }
    
    pub fn with_context_response(
        self,
        command: impl Into<String>,
        input: Option<String>,
        cwd: Option<String>,
        response: CommandResponse,
    ) -> Self {
        let context = CommandContext {
            command: command.into(),
            input,
            cwd,
        };
        self.inner.lock().unwrap().context_responses.insert(context, response);
        self
    }

    pub async fn execute(&self, command: &str) -> Result<CommandResponse> {
        self.execute_internal(command, None, None).await
    }
    
    async fn execute_internal(
        &self,
        command: &str,
        input: Option<&str>,
        cwd: Option<&Path>,
    ) -> Result<CommandResponse> {
        let mut inner = self.inner.lock().unwrap();
        
        if let Some(expectation) = inner.expectations.first() {
            expectation.call();
        }

        inner.command_history.push(CommandRecord {
            command: command.to_string(),
            input: input.map(|s| s.to_string()),
            cwd: cwd.map(|p| p.to_string_lossy().to_string()),
        });

        // First check context-specific responses
        let context = CommandContext {
            command: command.to_string(),
            input: input.map(|s| s.to_string()),
            cwd: cwd.map(|p| p.to_string_lossy().to_string()),
        };
        
        if let Some(response) = inner.context_responses.get(&context) {
            return Ok(response.clone());
        }

        // Fall back to simple command responses
        inner.responses
            .get(command)
            .cloned()
            .ok_or_else(|| anyhow::anyhow!("No response configured for command: {} (input: {:?}, cwd: {:?})", command, input, cwd))
    }

    pub fn get_history(&self) -> Vec<CommandRecord> {
        self.inner.lock().unwrap().command_history.clone()
    }

    pub fn expect_command(&self) -> Expectation {
        let expectation = Expectation::new();
        self.inner.lock().unwrap().expectations.push(expectation.clone());
        expectation
    }
}

#[async_trait::async_trait]
impl Shell for MockShell {
    async fn execute(&self, command: &str) -> Result<CommandOutput> {
        let response = self.execute_internal(command, None, None).await?;
        Ok(self.response_to_output(response))
    }

    async fn execute_with_cwd(&self, command: &str, cwd: Option<&Path>) -> Result<CommandOutput> {
        let response = self.execute_internal(command, None, cwd).await?;
        Ok(self.response_to_output(response))
    }

    async fn execute_with_env(
        &self,
        command: &str,
        cwd: Option<&Path>,
        _env: &[(String, String)],
    ) -> Result<CommandOutput> {
        // For simplicity, we ignore env in the mock
        self.execute_with_cwd(command, cwd).await
    }

    async fn execute_with_input(&self, command: &str, input: &str) -> Result<CommandOutput> {
        let response = self.execute_internal(command, Some(input), None).await?;
        Ok(self.response_to_output(response))
    }
    
    async fn execute_with_input_and_cwd(
        &self,
        command: &str,
        input: &str,
        cwd: Option<&Path>,
    ) -> Result<CommandOutput> {
        let response = self.execute_internal(command, Some(input), cwd).await?;
        Ok(self.response_to_output(response))
    }
}

impl MockShell {
    fn response_to_output(&self, response: CommandResponse) -> CommandOutput {
        CommandOutput {
            stdout: response.stdout,
            stderr: response.stderr,
            exit_code: response.exit_code,
            status: self.create_exit_status(response.exit_code),
        }
    }
    
    fn create_exit_status(&self, code: i32) -> ExitStatus {
        // This is a workaround since ExitStatus doesn't have a public constructor
        // In tests, we can use a dummy command to create the status
        std::process::Command::new("sh")
            .arg("-c")
            .arg(format!("exit {}", code))
            .status()
            .unwrap_or_else(|_| std::process::Command::new("true").status().unwrap())
    }
}

impl Mock<()> for MockShell {
    fn expect(&mut self) -> &mut Expectation {
        // This is a limitation of the current Mock trait design
        // We can't return a mutable reference from inside a Mutex
        unimplemented!("Use expect_command() instead")
    }

    fn checkpoint(&mut self) {
        let mut inner = self.inner.lock().unwrap();
        inner.expectations.clear();
        inner.command_history.clear();
    }

    fn verify(&self) -> Result<()> {
        let inner = self.inner.lock().unwrap();
        for expectation in &inner.expectations {
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
        let shell = MockShell::new()
            .with_response("echo hello", CommandResponse::success("hello\n"));

        let response = shell.execute("echo hello").await?;
        assert_eq!(response.stdout, "hello\n");
        assert_eq!(response.exit_code, 0);
        assert!(response.stderr.is_empty());

        Ok(())
    }

    #[tokio::test]
    async fn test_mock_shell_failure() -> Result<()> {
        let shell = MockShell::new()
            .with_response("false", CommandResponse::failure("Command failed", 1));

        let response = shell.execute("false").await?;
        assert_eq!(response.stderr, "Command failed");
        assert_eq!(response.exit_code, 1);
        assert!(response.stdout.is_empty());

        Ok(())
    }

    #[tokio::test]
    async fn test_mock_shell_history() -> Result<()> {
        let shell = MockShell::new()
            .with_response("echo one", CommandResponse::success("one\n"))
            .with_response("echo two", CommandResponse::success("two\n"));

        shell.execute("echo one").await?;
        shell.execute("echo two").await?;

        let history = shell.get_history();
        assert_eq!(history.len(), 2);
        assert_eq!(history[0].command, "echo one");
        assert_eq!(history[1].command, "echo two");

        Ok(())
    }

    #[tokio::test]
    async fn test_mock_shell_expectations() -> Result<()> {
        let shell = MockShell::new()
            .with_response("test", CommandResponse::success("ok"));

        let mut expectation = shell.expect_command();
        expectation.times(1);

        shell.execute("test").await?;
        
        shell.verify()?;
        Ok(())
    }
    
    #[tokio::test]
    async fn test_mock_shell_with_input_and_cwd() -> Result<()> {
        use crate::interfaces::shell::Shell;
        use std::path::PathBuf;
        
        let shell = MockShell::new()
            .with_context_response(
                "cat > output.txt",
                Some("Hello from input".to_string()),
                Some("/tmp/test".to_string()),
                CommandResponse::success(""),
            );

        let result = shell
            .execute_with_input_and_cwd(
                "cat > output.txt",
                "Hello from input",
                Some(&PathBuf::from("/tmp/test")),
            )
            .await?;

        assert_eq!(result.exit_code, 0);
        assert_eq!(result.stdout, "");
        assert_eq!(result.stderr, "");

        Ok(())
    }
    
    #[tokio::test]
    async fn test_mock_shell_fallback_to_simple_response() -> Result<()> {
        use crate::interfaces::shell::Shell;
        use std::path::PathBuf;
        
        // Test that context-aware commands fall back to simple responses when no context match
        let shell = MockShell::new()
            .with_response("echo test", CommandResponse::success("test\n"));

        // Execute with input and cwd, but should fall back to simple response
        let result = shell
            .execute_with_input_and_cwd(
                "echo test",
                "ignored input",
                Some(&PathBuf::from("/some/path")),
            )
            .await?;

        assert_eq!(result.exit_code, 0);
        assert_eq!(result.stdout, "test\n");

        Ok(())
    }
}