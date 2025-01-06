use tokio::sync::Mutex;
use std::sync::Arc;
use bollard::Docker;
use std::time::{Duration, Instant};
use tokio::time::sleep;
use tokio::time::timeout;
use futures::future::join_all;

use crate::docker::{DockerRunner, RunnerState, RunnerStatus};
use crate::config::Config;

const MAX_BUFFER_SIZE: usize = 1024 * 1024;  // 1MB
const OPERATION_TIMEOUT: Duration = Duration::from_secs(15);
const STOP_TIMEOUT: Duration = Duration::from_secs(10);

pub struct DockerRunners {
    docker: Docker,
    config: Arc<Config>,
    runners: Arc<Mutex<Vec<Arc<Mutex<DockerRunner>>>>>,
    connections: Arc<Mutex<Vec<Vec<usize>>>>,
    state: Arc<Mutex<RunnerState>>,
}

impl DockerRunners {
    pub fn new(docker: Docker, config: Config) -> Self {
        Self {
            docker,
            config: Arc::new(config),
            runners: Arc::new(Mutex::new(Vec::new())),
            connections: Arc::new(Mutex::new(Vec::new())),
            state: Arc::new(Mutex::new(RunnerState::new())),
        }
    }

    pub async fn add_runner(&self, language: String) -> Result<usize, String> {
        let mut runners = self.runners.lock().await;
        let mut connections = self.connections.lock().await;
        let mut state = self.state.lock().await;
        let id = runners.len();

        // 言語の存在確認
        let _resolved_lang = self.config.get_with_alias::<String>(&format!("{}.name", language))
            .map_err(|e| format!("言語名の解決に失敗しました: {}", e))?;

        let runner = DockerRunner::new(self.docker.clone(), self.config.clone(), language);
        runners.push(Arc::new(Mutex::new(runner)));
        connections.push(Vec::new());
        state.update_runner(id, RunnerStatus::Ready)?;

        Ok(id)
    }

    pub async fn run(&self) -> Result<(), String> {
        println!("Starting runner execution");
        {
            let mut state = self.state.lock().await;
            if state.get_status() != &RunnerStatus::Ready {
                return Err("実行準備ができていません".to_string());
            }
            state.start();
        }

        // タイムアウト設定の取得
        let timeout_seconds = self.config.get::<u64>("system.docker.timeout_seconds")
            .map_err(|e| format!("タイムアウト設定の読み込みに失敗しました: {}", e))?;
        let timeout = Duration::from_secs(timeout_seconds);
        let start = Instant::now();

        loop {
            if start.elapsed() > timeout {
                println!("Execution timeout reached after {:?}", start.elapsed());
                let mut state = self.state.lock().await;
                state.error(format!("実行がタイムアウトしました: {:?}", timeout));
                return Err(format!("実行がタイムアウトしました: {:?}", timeout));
            }

            if !self.check_runners(None).await {
                println!("Runner error detected");
                let mut state = self.state.lock().await;
                state.error("ランナーでエラーが発生しました".to_string());
                return Err("ランナーでエラーが発生しました".to_string());
            }

            // 他のチェックロジック...

            sleep(Duration::from_millis(100)).await;
        }
    }

    // 他のメソッドは必要に応じて更新...
} 