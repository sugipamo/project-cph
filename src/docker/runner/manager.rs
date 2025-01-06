use tokio::sync::Mutex;
use std::sync::Arc;
use std::time::{Duration, Instant};

use crate::docker::{DockerRunner, RunnerState, DefaultDockerExecutor};
use crate::docker::traits::ContainerManager;
use crate::config::Config;

const OPERATION_TIMEOUT: Duration = Duration::from_secs(15);

pub struct DockerRunnerManager {
    config: Arc<Config>,
    runners: Arc<Mutex<Vec<Arc<Mutex<DockerRunner>>>>>,
    connections: Arc<Mutex<Vec<Vec<usize>>>>,
    state: Arc<Mutex<RunnerState>>,
    container_manager: Arc<Mutex<dyn ContainerManager>>,
}

impl DockerRunnerManager {
    pub fn new(config: Config, container_manager: Arc<Mutex<dyn ContainerManager>>) -> Self {
        Self {
            config: Arc::new(config),
            runners: Arc::new(Mutex::new(Vec::new())),
            connections: Arc::new(Mutex::new(Vec::new())),
            state: Arc::new(Mutex::new(RunnerState::Created {
                container_id: String::new(),
                created_at: Instant::now(),
            })),
            container_manager,
        }
    }

    pub async fn add_runner(&self, language: String) -> Result<usize, String> {
        let mut runners = self.runners.lock().await;
        let mut connections = self.connections.lock().await;
        let id = runners.len();

        // 言語の存在確認
        let _resolved_lang = self.config.get_with_alias::<String>(&format!("{}.name", language))
            .map_err(|e| format!("言語名の解決に失敗しました: {}", e))?;

        let runner = DockerRunner::new(
            self.container_manager.clone(),
            Arc::new(DefaultDockerExecutor::new()),
            OPERATION_TIMEOUT,
        );
        runners.push(Arc::new(Mutex::new(runner)));
        connections.push(Vec::new());

        Ok(id)
    }
} 