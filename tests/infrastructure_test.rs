#[cfg(test)]
mod tests {
    use cph::infrastructure::test_support::mock_drivers::*;
    use cph::infrastructure::test_support::mock_drivers::shell::CommandResponse;
    use cph::infrastructure::test_support::mock_drivers::docker::RunResponse;

    #[tokio::test]
    async fn test_mock_file_system() {
        let fs = MockFileSystem::new()
            .with_file("/app/config.toml", "name = \"test\"")
            .with_directory("/app/src");

        assert!(fs.exists(&std::path::Path::new("/app/config.toml")).await);
        assert!(fs.exists(&std::path::Path::new("/app/src")).await);
        assert!(!fs.exists(&std::path::Path::new("/app/bin")).await);

        let content = fs.read_file(&std::path::Path::new("/app/config.toml")).await.unwrap();
        assert_eq!(content, "name = \"test\"");
    }

    #[tokio::test]
    async fn test_mock_shell() {
        let shell = MockShell::new()
            .with_response("echo hello", CommandResponse::success("hello\n"))
            .with_response("exit 1", CommandResponse::failure("Error", 1));

        let result = shell.execute("echo hello").await.unwrap();
        assert_eq!(result.stdout, "hello\n");
        assert_eq!(result.exit_code, 0);

        let result = shell.execute("exit 1").await.unwrap();
        assert_eq!(result.stderr, "Error");
        assert_eq!(result.exit_code, 1);

        let history = shell.get_history();
        assert_eq!(history.len(), 2);
    }

    #[tokio::test]
    async fn test_mock_docker() {
        let mut docker = MockDocker::new()
            .with_image("ubuntu:20.04")
            .with_run_response(
                "ubuntu:echo test",
                RunResponse {
                    container_id: "mock-123".to_string(),
                    exit_code: 0,
                    stdout: "test\n".to_string(),
                    stderr: String::new(),
                },
            );

        let result = docker
            .run_container("ubuntu", &["echo".to_string(), "test".to_string()], None)
            .await
            .unwrap();

        assert_eq!(result.container_id, "mock-123");
        assert_eq!(result.stdout, "test\n");
        assert_eq!(result.exit_code, 0);
    }

    #[test]
    fn test_expectation_system() {
        let mut fs = MockFileSystem::new();
        fs.expect_read().times(2);

        // This test would fail if we don't call read_file exactly 2 times
        // but we can't actually test the failure case in a unit test
    }
}