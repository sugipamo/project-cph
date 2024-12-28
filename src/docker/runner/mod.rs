mod container;
pub mod io;
mod compiler;

use std::sync::Arc;
use tokio::sync::Mutex;
use bollard::Docker;
use std::time::Instant;

use crate::docker::config::RunnerConfig;
use crate::docker::error::Result;
use crate::docker::state::RunnerState;
use crate::docker::runner::io::DockerOutput;

pub struct DockerRunner {
    docker: Docker,
    container_id: String,
    state: Arc<Mutex<RunnerState>>,
    stdout_buffer: Arc<Mutex<Vec<String>>>,
    stderr_buffer: Arc<Mutex<Vec<String>>>,
    stdin_tx: Option<tokio::sync::mpsc::Sender<String>>,
    config: RunnerConfig,
    language: String,
}

impl DockerRunner {
    pub fn new(docker: Docker, config: RunnerConfig, language: String) -> Self {
        Self {
            docker,
            container_id: String::new(),
            state: Arc::new(Mutex::new(RunnerState::Ready)),
            stdout_buffer: Arc::new(Mutex::new(Vec::new())),
            stderr_buffer: Arc::new(Mutex::new(Vec::new())),
            stdin_tx: None,
            config,
            language,
        }
    }

    pub async fn get_state(&self) -> RunnerState {
        self.state.lock().await.clone()
    }

    pub async fn run_in_docker(&mut self, source_code: &str) -> Result<DockerOutput> {
        let start = Instant::now();

        // コンテナの初期化と実行
        self.initialize(source_code).await?;

        // 初期の標準出力と標準エラー出力を取得
        let stdout = self.read_all().await?;
        let stderr = self.read_error_all().await?;

        Ok(DockerOutput {
            stdout: stdout.join("\n"),
            stderr: stderr.join("\n"),
            execution_time: start.elapsed(),
        })
    }
} 