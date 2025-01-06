use async_trait::async_trait;
use tokio::sync::mpsc;
use tokio::time::timeout;
use std::time::Duration;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::collections::HashMap;

use crate::docker::error::{DockerError, DockerResult};
use crate::docker::traits::{ContainerManager, IOHandler, CompilationManager};
use crate::docker::executor::{DockerCommand, DockerCommandExecutor, CommandOutput};
use crate::docker::runner::io::ContainerIO;

pub struct DefaultContainerManager {
    container_id: String,
    memory_limit: u64,
    mount_point: String,
    docker_executor: Arc<dyn DockerCommandExecutor>,
}

impl DefaultContainerManager {
    pub fn new(memory_limit: u64, mount_point: String, executor: Arc<dyn DockerCommandExecutor>) -> Self {
        Self {
            container_id: String::new(),
            memory_limit,
            mount_point,
            docker_executor: executor,
        }
    }

    async fn ensure_container_exists(&self) -> DockerResult<()> {
        if self.container_id.is_empty() {
            return Err(DockerError::Container("コンテナが作成されていません".to_string()));
        }
        Ok(())
    }
}

#[async_trait]
impl ContainerManager for DefaultContainerManager {
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> DockerResult<()> {
        if !self.container_id.is_empty() {
            return Err(DockerError::Container("コンテナは既に作成されています".to_string()));
        }

        let command = DockerCommand::new("create")
            .arg("-i")
            .arg("--rm")
            .arg("-m")
            .arg(format!("{}m", self.memory_limit))
            .arg("-v")
            .arg(format!("{}:{}", self.mount_point, working_dir))
            .arg("-w")
            .arg(working_dir)
            .arg(image)
            .args(cmd);

        let output = self.docker_executor.execute(command).await?;

        if output.success {
            self.container_id = output.stdout.trim().to_string();
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "コンテナの作成に失敗しました: {}",
                output.stderr
            )))
        }
    }

    async fn start_container(&mut self) -> DockerResult<()> {
        self.ensure_container_exists().await?;

        let command = DockerCommand::new("start")
            .arg(&self.container_id);

        let output = self.docker_executor.execute(command).await?;

        if output.success {
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "コンテナの起動に失敗しました: {}",
                output.stderr
            )))
        }
    }

    async fn stop_container(&mut self) -> DockerResult<()> {
        if self.container_id.is_empty() {
            return Ok(());
        }

        let command = DockerCommand::new("stop")
            .arg(&self.container_id);

        let output = self.docker_executor.execute(command).await?;

        if output.success {
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "コンテナの停止に失敗しました: {}",
                output.stderr
            )))
        }
    }

    async fn get_container_id(&self) -> DockerResult<String> {
        self.ensure_container_exists().await?;
        Ok(self.container_id.clone())
    }

    async fn get_exit_code(&self) -> DockerResult<i32> {
        self.ensure_container_exists().await?;

        let command = DockerCommand::new("inspect")
            .arg("--format={{.State.ExitCode}}")
            .arg(&self.container_id);

        let output = self.docker_executor.execute(command).await?;
        if output.success {
            output.stdout.trim().parse::<i32>()
                .map_err(|e| DockerError::Container(format!("終了コードの解析に失敗しました: {}", e)))
        } else {
            Err(DockerError::Container(format!(
                "終了コードの取得に失敗しました: {}",
                output.stderr
            )))
        }
    }

    async fn check_image(&self, image: &str) -> DockerResult<bool> {
        let command = DockerCommand::new("image")
            .arg("inspect")
            .arg(image);

        let output = self.docker_executor.execute(command).await?;
        Ok(output.success)
    }

    async fn pull_image(&self, image: &str) -> DockerResult<()> {
        let command = DockerCommand::new("pull")
            .arg(image);

        let output = self.docker_executor.execute(command).await?;

        if output.success {
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "イメージの取得に失敗しました: {}",
                output.stderr
            )))
        }
    }
}

pub struct DefaultCompilationManager {
    container_id: String,
    working_dir: String,
    docker_executor: Arc<dyn DockerCommandExecutor>,
}

impl DefaultCompilationManager {
    pub fn new(container_id: String, working_dir: String, executor: Arc<dyn DockerCommandExecutor>) -> Self {
        Self {
            container_id,
            working_dir,
            docker_executor: executor,
        }
    }
}

#[async_trait]
impl CompilationManager for DefaultCompilationManager {
    async fn compile(
        &mut self,
        source_code: &str,
        compile_cmd: Option<Vec<String>>,
        env_vars: Vec<String>,
    ) -> DockerResult<()> {
        if let Some(cmd) = compile_cmd {
            let mut command = DockerCommand::new("exec")
                .arg("-i")
                .arg(&self.container_id)
                .args(cmd);

            // 環境変数の設定
            for env_var in env_vars {
                let parts: Vec<&str> = env_var.split('=').collect();
                if parts.len() == 2 {
                    command = command.env(parts[0], parts[1]);
                }
            }

            let output = self.docker_executor.execute(command).await?;

            if !output.success {
                return Err(DockerError::Compilation(format!(
                    "コンパイルに失敗しました: {}",
                    output.stderr
                )));
            }
        }
        Ok(())
    }

    async fn get_compilation_output(&self) -> DockerResult<(String, String)> {
        let stdout_command = DockerCommand::new("logs")
            .arg(&self.container_id);
        let stdout_output = self.docker_executor.execute(stdout_command).await?;

        let stderr_command = DockerCommand::new("logs")
            .arg("--stderr")
            .arg(&self.container_id);
        let stderr_output = self.docker_executor.execute(stderr_command).await?;

        Ok((stdout_output.stdout, stderr_output.stderr))
    }
}

pub struct DefaultDockerCommandExecutor;

impl DefaultDockerCommandExecutor {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait]
impl DockerCommandExecutor for DefaultDockerCommandExecutor {
    async fn execute_command(&self, args: Vec<String>) -> DockerResult<(bool, String, String)> {
        let output = Command::new("docker")
            .args(&args)
            .output()
            .map_err(|e| DockerError::Container(format!("Dockerコマンドの実行に失敗しました: {}", e)))?;

        Ok((
            output.status.success(),
            String::from_utf8_lossy(&output.stdout).to_string(),
            String::from_utf8_lossy(&output.stderr).to_string(),
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;
    use crate::docker::error::DockerError;
    use crate::docker::executor::{DockerCommand, CommandOutput};

    mock! {
        DockerExecutor {}
        #[async_trait]
        impl DockerCommandExecutor for DockerExecutor {
            async fn execute(&self, command: DockerCommand) -> DockerResult<CommandOutput>;
        }
    }

    #[tokio::test]
    async fn test_default_container_manager_create() {
        let mut mock_executor = MockDockerExecutor::new();
        mock_executor
            .expect_execute()
            .returning(|_| Ok(CommandOutput {
                success: true,
                stdout: "container_id".to_string(),
                stderr: "".to_string(),
            }));

        let mut manager = DefaultContainerManager {
            container_id: String::new(),
            memory_limit: 512,
            mount_point: "/tmp".to_string(),
            docker_executor: Arc::new(mock_executor),
        };

        let result = manager.create_container(
            "test-image",
            vec!["test".to_string()],
            "/workspace",
        ).await;

        assert!(result.is_ok());
        assert_eq!(manager.container_id, "container_id");
    }

    #[tokio::test]
    async fn test_default_container_manager_start() {
        let mut mock_executor = MockDockerExecutor::new();
        mock_executor
            .expect_execute()
            .returning(|_| Ok(CommandOutput {
                success: true,
                stdout: "".to_string(),
                stderr: "".to_string(),
            }));

        let mut manager = DefaultContainerManager {
            container_id: "test_container".to_string(),
            memory_limit: 512,
            mount_point: "/tmp".to_string(),
            docker_executor: Arc::new(mock_executor),
        };

        let result = manager.start_container().await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_default_container_manager_error() {
        let mut mock_executor = MockDockerExecutor::new();
        mock_executor
            .expect_execute()
            .returning(|_| Ok(CommandOutput {
                success: false,
                stdout: "".to_string(),
                stderr: "Error message".to_string(),
            }));

        let mut manager = DefaultContainerManager {
            container_id: "test_container".to_string(),
            memory_limit: 512,
            mount_point: "/tmp".to_string(),
            docker_executor: Arc::new(mock_executor),
        };

        let result = manager.start_container().await;
        assert!(result.is_err());
        match result {
            Err(DockerError::Container(msg)) => assert!(msg.contains("Error message")),
            _ => panic!("Expected Container error"),
        }
    }

    #[tokio::test]
    async fn test_default_io_handler() {
        let mut mock_executor = MockDockerExecutor::new();
        mock_executor
            .expect_execute()
            .returning(|_| Ok(CommandOutput {
                success: true,
                stdout: "output".to_string(),
                stderr: "".to_string(),
            }));

        let handler = DefaultIOHandler {
            container_id: "test_container".to_string(),
            stdout_buffer: Arc::new(Mutex::new(Vec::new())),
            stderr_buffer: Arc::new(Mutex::new(Vec::new())),
            stdin_tx: None,
            docker_executor: Arc::new(mock_executor),
        };

        let result = handler.read_stdout(Duration::from_secs(1)).await;
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "output");
    }

    #[tokio::test]
    async fn test_default_compilation_manager() {
        let mut mock_executor = MockDockerExecutor::new();
        mock_executor
            .expect_execute()
            .returning(|_| Ok(CommandOutput {
                success: true,
                stdout: "".to_string(),
                stderr: "".to_string(),
            }));

        let mut manager = DefaultCompilationManager {
            container_id: "test_container".to_string(),
            working_dir: "/workspace".to_string(),
            docker_executor: Arc::new(mock_executor),
        };

        let result = manager.compile(
            "test code",
            Some(vec!["gcc".to_string(), "-o".to_string(), "test".to_string()]),
            vec![],
        ).await;

        assert!(result.is_ok());
    }
} 