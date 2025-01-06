use async_trait::async_trait;
use tokio::sync::mpsc;
use tokio::time::timeout;
use std::time::Duration;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::process::Command;

use crate::docker::error::{DockerError, DockerResult};
use crate::docker::traits::{ContainerManager, IOHandler, CompilationManager};

pub struct DefaultContainerManager {
    container_id: String,
    memory_limit: u64,
    mount_point: String,
}

impl DefaultContainerManager {
    pub fn new(memory_limit: u64, mount_point: String) -> Self {
        Self {
            container_id: String::new(),
            memory_limit,
            mount_point,
        }
    }
}

#[async_trait]
impl ContainerManager for DefaultContainerManager {
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> DockerResult<()> {
        let output = Command::new("docker")
            .args(["create", "-i", "--rm"])
            .args(["-m", &format!("{}m", self.memory_limit)])
            .args(["-v", &format!("{}:{}", self.mount_point, working_dir)])
            .args(["-w", working_dir])
            .arg(image)
            .args(cmd)
            .output()
            .map_err(|e| DockerError::Container(format!("コンテナの作成に失敗しました: {}", e)))?;

        if output.status.success() {
            self.container_id = String::from_utf8_lossy(&output.stdout).trim().to_string();
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "コンテナの作成に失敗しました: {}",
                String::from_utf8_lossy(&output.stderr)
            )))
        }
    }

    async fn start_container(&mut self) -> DockerResult<()> {
        let output = Command::new("docker")
            .args(["start", &self.container_id])
            .output()
            .map_err(|e| DockerError::Container(format!("コンテナの起動に失敗しました: {}", e)))?;

        if output.status.success() {
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "コンテナの起動に失敗しました: {}",
                String::from_utf8_lossy(&output.stderr)
            )))
        }
    }

    async fn stop_container(&mut self) -> DockerResult<()> {
        if !self.container_id.is_empty() {
            let output = Command::new("docker")
                .args(["stop", &self.container_id])
                .output()
                .map_err(|e| DockerError::Container(format!("コンテナの停止に失敗しました: {}", e)))?;

            if !output.status.success() {
                return Err(DockerError::Container(format!(
                    "コンテナの停止に失敗しました: {}",
                    String::from_utf8_lossy(&output.stderr)
                )));
            }
        }
        Ok(())
    }

    async fn check_image(&self, image: &str) -> DockerResult<bool> {
        let output = Command::new("docker")
            .args(["image", "inspect", image])
            .output()
            .map_err(|e| DockerError::Container(format!("イメージの確認に失敗しました: {}", e)))?;

        Ok(output.status.success())
    }

    async fn pull_image(&self, image: &str) -> DockerResult<()> {
        let output = Command::new("docker")
            .args(["pull", image])
            .output()
            .map_err(|e| DockerError::Container(format!("イメージの取得に失敗しました: {}", e)))?;

        if output.status.success() {
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "イメージの取得に失敗しました: {}",
                String::from_utf8_lossy(&output.stderr)
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