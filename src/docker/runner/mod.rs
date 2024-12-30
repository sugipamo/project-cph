mod container;
pub mod io;
mod compiler;

use std::sync::Arc;
use tokio::sync::Mutex;
use bollard::Docker;
use std::time::Duration;

use crate::docker::error::{DockerError, Result};
use crate::docker::state::RunnerState;
use crate::docker::config::RunnerConfig;

pub struct DockerRunner {
    docker: Docker,
    config: RunnerConfig,
    container_id: String,
    language: String,
    state: Arc<Mutex<RunnerState>>,
    stdin_tx: Option<tokio::sync::mpsc::Sender<String>>,
    stdout_buffer: Arc<Mutex<Vec<String>>>,
    stderr_buffer: Arc<Mutex<Vec<String>>>,
}

impl DockerRunner {
    pub fn new(docker: Docker, config: RunnerConfig, language: String) -> Self {
        Self {
            docker,
            config,
            container_id: String::new(),
            language,
            state: Arc::new(Mutex::new(RunnerState::Ready)),
            stdin_tx: None,
            stdout_buffer: Arc::new(Mutex::new(Vec::new())),
            stderr_buffer: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub async fn run_in_docker(&mut self, source_code: &str) -> Result<()> {
        println!("Starting Docker execution for language: {}", self.language);
        
        // 初期化
        self.initialize(source_code).await?;
        println!("Container initialized successfully");

        // 実行結果の取得
        let stdout = self.read().await?;
        let stderr = self.read_error().await?;
        
        if !stderr.is_empty() {
            println!("Execution produced errors: {}", stderr);
            *self.state.lock().await = RunnerState::Error;
            return Err(DockerError::RuntimeError(stderr));
        }

        println!("Execution completed successfully");
        println!("Output: {}", stdout);
        Ok(())
    }

    pub async fn get_state(&self) -> RunnerState {
        self.state.lock().await.clone()
    }
} 