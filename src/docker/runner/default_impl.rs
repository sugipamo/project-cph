use async_trait::async_trait;
use tokio::sync::mpsc;
use tokio::time::timeout;
use std::time::Duration;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::process::Command;
use std::collections::HashMap;

use crate::docker::error::{DockerError, DockerResult};
use crate::docker::traits::{ContainerManager, IOHandler, CompilationManager, DockerCommandExecutor};

pub struct DefaultContainerManager {
    container_id: String,
    memory_limit: u64,
    mount_point: String,
    docker_executor: Box<dyn DockerCommandExecutor>,
}

impl DefaultContainerManager {
    pub fn new(memory_limit: u64, mount_point: String) -> Self {
        Self {
            container_id: String::new(),
            memory_limit,
            mount_point,
            docker_executor: Box::new(DefaultDockerCommandExecutor::new()),
        }
    }

    pub fn with_executor(memory_limit: u64, mount_point: String, executor: Box<dyn DockerCommandExecutor>) -> Self {
        Self {
            container_id: String::new(),
            memory_limit,
            mount_point,
            docker_executor: executor,
        }
    }
}

#[async_trait]
impl ContainerManager for DefaultContainerManager {
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> DockerResult<()> {
        let mut args = vec![
            "create".to_string(),
            "-i".to_string(),
            "--rm".to_string(),
            "-m".to_string(),
            format!("{}m", self.memory_limit),
            "-v".to_string(),
            format!("{}:{}", self.mount_point, working_dir),
            "-w".to_string(),
            working_dir.to_string(),
            image.to_string(),
        ];
        args.extend(cmd);

        let (success, stdout, stderr) = self.docker_executor.execute_command(args).await?;

        if success {
            self.container_id = stdout.trim().to_string();
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "コンテナの作成に失敗しました: {}",
                stderr
            )))
        }
    }

    async fn start_container(&mut self) -> DockerResult<()> {
        let args = vec!["start".to_string(), self.container_id.clone()];
        let (success, _, stderr) = self.docker_executor.execute_command(args).await?;

        if success {
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "コンテナの起動に失敗しました: {}",
                stderr
            )))
        }
    }

    async fn stop_container(&mut self) -> DockerResult<()> {
        if !self.container_id.is_empty() {
            let args = vec!["stop".to_string(), self.container_id.clone()];
            let (success, _, stderr) = self.docker_executor.execute_command(args).await?;

            if !success {
                return Err(DockerError::Container(format!(
                    "コンテナの停止に失敗しました: {}",
                    stderr
                )));
            }
        }
        Ok(())
    }

    async fn check_image(&self, image: &str) -> DockerResult<bool> {
        let args = vec!["image".to_string(), "inspect".to_string(), image.to_string()];
        let (success, _, _) = self.docker_executor.execute_command(args).await?;
        Ok(success)
    }

    async fn pull_image(&self, image: &str) -> DockerResult<()> {
        let args = vec!["pull".to_string(), image.to_string()];
        let (success, _, stderr) = self.docker_executor.execute_command(args).await?;

        if success {
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "イメージの取得に失敗しました: {}",
                stderr
            )))
        }
    }
}

pub struct DefaultIOHandler {
    container_id: String,
    stdout_buffer: Arc<Mutex<Vec<String>>>,
    stderr_buffer: Arc<Mutex<Vec<String>>>,
    stdin_tx: Option<mpsc::Sender<String>>,
}

impl DefaultIOHandler {
    pub fn new(container_id: String) -> Self {
        Self {
            container_id,
            stdout_buffer: Arc::new(Mutex::new(Vec::new())),
            stderr_buffer: Arc::new(Mutex::new(Vec::new())),
            stdin_tx: None,
        }
    }
}

#[async_trait]
impl IOHandler for DefaultIOHandler {
    async fn write(&self, input: &str) -> DockerResult<()> {
        let output = Command::new("docker")
            .args(["exec", "-i", &self.container_id])
            .arg("sh")
            .arg("-c")
            .arg(input)
            .output()
            .map_err(|e| DockerError::IO(format!("入力の送信に失敗しました: {}", e)))?;

        if output.status.success() {
            Ok(())
        } else {
            Err(DockerError::IO(format!(
                "入力の送信に失敗しました: {}",
                String::from_utf8_lossy(&output.stderr)
            )))
        }
    }

    async fn read_stdout(&self, timeout_duration: Duration) -> DockerResult<String> {
        let output = Command::new("docker")
            .args(["logs", &self.container_id])
            .output()
            .map_err(|e| DockerError::IO(format!("標準出力の読み取りに失敗しました: {}", e)))?;

        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    }

    async fn read_stderr(&self, timeout_duration: Duration) -> DockerResult<String> {
        let output = Command::new("docker")
            .args(["logs", "--stderr", &self.container_id])
            .output()
            .map_err(|e| DockerError::IO(format!("標準エラー出力の読み取りに失敗しました: {}", e)))?;

        Ok(String::from_utf8_lossy(&output.stderr).to_string())
    }

    async fn setup_io(&mut self) -> DockerResult<()> {
        Ok(())
    }
}

pub struct DefaultCompilationManager {
    container_id: String,
    working_dir: String,
}

impl DefaultCompilationManager {
    pub fn new(container_id: String, working_dir: String) -> Self {
        Self {
            container_id,
            working_dir,
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
            let output = Command::new("docker")
                .args(["exec", "-i", &self.container_id])
                .args(cmd)
                .current_dir(&self.working_dir)
                .envs(env_vars.iter().map(|s| {
                    let parts: Vec<&str> = s.split('=').collect();
                    (parts[0], parts[1])
                }))
                .output()
                .map_err(|e| DockerError::Compilation(format!("コンパイルに失敗しました: {}", e)))?;

            if !output.status.success() {
                return Err(DockerError::Compilation(format!(
                    "コンパイルに失敗しました: {}",
                    String::from_utf8_lossy(&output.stderr)
                )));
            }
        }
        Ok(())
    }

    async fn get_compilation_output(&self) -> DockerResult<(String, String)> {
        let stdout = Command::new("docker")
            .args(["logs", &self.container_id])
            .output()
            .map_err(|e| DockerError::IO(format!("コンパイル出力の読み取りに失敗しました: {}", e)))?;

        let stderr = Command::new("docker")
            .args(["logs", "--stderr", &self.container_id])
            .output()
            .map_err(|e| DockerError::IO(format!("コンパイルエラーの読み取りに失敗しました: {}", e)))?;

        Ok((
            String::from_utf8_lossy(&stdout.stdout).to_string(),
            String::from_utf8_lossy(&stderr.stderr).to_string(),
        ))
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

    // DockerCommandExecutorのモック
    mock! {
        DockerCommandExecutor {}
        #[async_trait]
        impl DockerCommandExecutor for DockerCommandExecutor {
            async fn execute_command(&self, args: Vec<String>) -> DockerResult<(bool, String, String)>;
        }
    }

    #[tokio::test]
    async fn test_default_container_manager_create() {
        let mut mock_executor = MockDockerCommandExecutor::new();
        mock_executor
            .expect_execute_command()
            .returning(|_| Ok((true, "container_id".to_string(), "".to_string())));

        let mut manager = DefaultContainerManager {
            container_id: String::new(),
            memory_limit: 512,
            mount_point: "/tmp".to_string(),
            docker_executor: Box::new(mock_executor),
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
        let mut mock_executor = MockDockerCommandExecutor::new();
        mock_executor
            .expect_execute_command()
            .returning(|_| Ok((true, "".to_string(), "".to_string())));

        let mut manager = DefaultContainerManager {
            container_id: "test_container".to_string(),
            memory_limit: 512,
            mount_point: "/tmp".to_string(),
            docker_executor: Box::new(mock_executor),
        };

        let result = manager.start_container().await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_default_container_manager_error() {
        let mut mock_executor = MockDockerCommandExecutor::new();
        mock_executor
            .expect_execute_command()
            .returning(|_| Ok((false, "".to_string(), "Error message".to_string())));

        let mut manager = DefaultContainerManager {
            container_id: "test_container".to_string(),
            memory_limit: 512,
            mount_point: "/tmp".to_string(),
            docker_executor: Box::new(mock_executor),
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
        let mut mock_executor = MockDockerCommandExecutor::new();
        mock_executor
            .expect_execute_command()
            .returning(|_| Ok((true, "output".to_string(), "".to_string())));

        let handler = DefaultIOHandler {
            container_id: "test_container".to_string(),
            docker_executor: Box::new(mock_executor),
        };

        let result = handler.read_stdout(Duration::from_secs(1)).await;
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "output");
    }

    #[tokio::test]
    async fn test_default_compilation_manager() {
        let mut mock_executor = MockDockerCommandExecutor::new();
        mock_executor
            .expect_execute_command()
            .returning(|_| Ok((true, "".to_string(), "".to_string())));

        let mut manager = DefaultCompilationManager {
            container_id: "test_container".to_string(),
            docker_executor: Box::new(mock_executor),
            compilation_output: None,
        };

        let result = manager.compile(
            "test code",
            Some(vec!["gcc".to_string(), "-o".to_string(), "test".to_string()]),
            vec![],
        ).await;

        assert!(result.is_ok());
    }
} 