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
    use std::sync::Arc;
    use tokio::sync::Mutex;
    use std::collections::HashMap;

    struct TestDockerExecutor {
        responses: Arc<Mutex<HashMap<String, (bool, String, String)>>>,
    }

    impl TestDockerExecutor {
        fn new() -> Self {
            Self {
                responses: Arc::new(Mutex::new(HashMap::new())),
            }
        }

        async fn set_response(&self, args: Vec<String>, response: (bool, String, String)) {
            let key = args.join(" ");
            self.responses.lock().await.insert(key, response);
        }
    }

    #[async_trait]
    impl DockerCommandExecutor for TestDockerExecutor {
        async fn execute_command(&self, args: Vec<String>) -> DockerResult<(bool, String, String)> {
            let key = args.join(" ");
            let responses = self.responses.lock().await;
            
            match responses.get(&key) {
                Some(response) => Ok(response.clone()),
                None => Ok((true, String::new(), String::new())),
            }
        }
    }

    #[tokio::test]
    async fn test_container_lifecycle() {
        let executor = TestDockerExecutor::new();
        
        // create_containerのレスポンスを設定
        executor
            .set_response(
                vec![
                    "create".to_string(),
                    "-i".to_string(),
                    "--rm".to_string(),
                    "-m".to_string(),
                    "512m".to_string(),
                    "-v".to_string(),
                    "/tmp:/workspace".to_string(),
                    "-w".to_string(),
                    "/workspace".to_string(),
                    "test-image".to_string(),
                    "test-cmd".to_string(),
                ],
                (true, "test-container-id".to_string(), String::new()),
            )
            .await;

        let mut manager = DefaultContainerManager::with_executor(
            512,
            "/tmp".to_string(),
            Box::new(executor),
        );

        // コンテナの作成
        let result = manager
            .create_container(
                "test-image",
                vec!["test-cmd".to_string()],
                "/workspace",
            )
            .await;
        assert!(result.is_ok());
        assert_eq!(manager.container_id, "test-container-id");

        // コンテナの起動
        let result = manager.start_container().await;
        assert!(result.is_ok());

        // コンテナの停止
        let result = manager.stop_container().await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_image_operations() {
        let executor = TestDockerExecutor::new();
        let manager = DefaultContainerManager::with_executor(
            512,
            "/tmp".to_string(),
            Box::new(executor),
        );

        // イメージの確認
        let result = manager.check_image("test-image").await;
        assert!(result.is_ok());
        assert!(result.unwrap());

        // イメージの取得
        let result = manager.pull_image("test-image").await;
        assert!(result.is_ok());
    }
} 