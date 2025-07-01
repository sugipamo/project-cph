#[cfg(test)]
mod tests {
    use cph::infrastructure::test_support::mock_drivers::{MockShell, shell::CommandResponse};
    use cph::interfaces::shell::Shell;
    use std::path::PathBuf;
    use std::sync::Arc;

    // This function accepts any Shell implementation
    async fn run_command_with_shell(shell: Arc<dyn Shell>) -> anyhow::Result<String> {
        let output = shell.execute("echo test").await?;
        Ok(output.stdout)
    }

    // This function uses execute_with_input_and_cwd
    async fn run_complex_command(shell: Arc<dyn Shell>) -> anyhow::Result<i32> {
        let output = shell
            .execute_with_input_and_cwd(
                "cat > file.txt",
                "test content",
                Some(&PathBuf::from("/tmp")),
            )
            .await?;
        Ok(output.exit_code)
    }

    #[tokio::test]
    async fn test_mock_shell_as_trait_object() {
        let mock_shell = MockShell::new()
            .with_response("echo test", CommandResponse::success("test\n"));
        
        let shell: Arc<dyn Shell> = Arc::new(mock_shell);
        
        let result = run_command_with_shell(shell).await.unwrap();
        assert_eq!(result, "test\n");
    }

    #[tokio::test]
    async fn test_mock_shell_complex_command_as_trait() {
        let mock_shell = MockShell::new()
            .with_context_response(
                "cat > file.txt",
                Some("test content".to_string()),
                Some("/tmp".to_string()),
                CommandResponse::success(""),
            );
        
        let shell: Arc<dyn Shell> = Arc::new(mock_shell);
        
        let exit_code = run_complex_command(shell).await.unwrap();
        assert_eq!(exit_code, 0);
    }
}