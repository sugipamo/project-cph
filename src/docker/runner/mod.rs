use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::Mutex;

use crate::docker::error::{DockerError, DockerResult};
use crate::docker::traits::DockerOperations;
use crate::docker::state::{ContainerState, StateManager, StateError};
use crate::docker::config::ContainerConfig;
use crate::docker::executor::{DockerCommand, DockerCommandExecutor};

pub struct DockerRunner {
    operations: Arc<Mutex<dyn DockerOperations>>,
    state_manager: Arc<Mutex<StateManager>>,
    timeout: Duration,
    docker_executor: Arc<dyn DockerCommandExecutor>,
}

impl DockerRunner {
    pub fn new(
        operations: Arc<Mutex<dyn DockerOperations>>,
        docker_executor: Arc<dyn DockerCommandExecutor>,
        timeout: Duration
    ) -> Self {
        Self {
            operations,
            state_manager: Arc::new(Mutex::new(StateManager::new())),
            timeout,
            docker_executor,
        }
    }

    pub async fn initialize(&mut self, config: ContainerConfig) -> DockerResult<()> {
        let mut ops = self.operations.lock().await;
        ops.initialize(config).await?;

        let mut state_manager = self.state_manager.lock().await;
        state_manager.transition_to(ContainerState::Created {
            container_id: self.get_container_id().await?,
            created_at: Instant::now(),
        }).await.map_err(DockerError::State)?;

        Ok(())
    }

    pub async fn start(&mut self) -> DockerResult<()> {
        let mut ops = self.operations.lock().await;
        ops.start().await?;

        let mut state_manager = self.state_manager.lock().await;
        state_manager.transition_to(ContainerState::Running {
            container_id: self.get_container_id().await?,
            started_at: Instant::now(),
        }).await.map_err(DockerError::State)?;

        Ok(())
    }

    pub async fn stop(&mut self) -> DockerResult<()> {
        let mut ops = self.operations.lock().await;
        ops.stop().await?;

        let mut state_manager = self.state_manager.lock().await;
        let current_state = state_manager.get_current_state();
        let execution_time = current_state.duration_since_start().unwrap_or_default();

        state_manager.transition_to(ContainerState::Stopped {
            container_id: self.get_container_id().await?,
            exit_code: 0, // TODO: 実際の終了コードを取得
            execution_time,
        }).await.map_err(DockerError::State)?;

        Ok(())
    }

    pub async fn execute(&mut self, command: &str) -> DockerResult<(String, String)> {
        let container_id = self.get_container_id().await?;
        let mut state_manager = self.state_manager.lock().await;

        // 実行状態に遷移
        state_manager.transition_to(ContainerState::Executing {
            container_id: container_id.clone(),
            started_at: Instant::now(),
            command: command.to_string(),
        }).await.map_err(DockerError::State)?;

        // コマンドを実行
        let mut ops = self.operations.lock().await;
        let result = ops.execute(command).await;

        // 結果に応じて状態を更新
        match &result {
            Ok(_) => {
                state_manager.transition_to(ContainerState::Running {
                    container_id,
                    started_at: Instant::now(),
                }).await.map_err(DockerError::State)?;
            }
            Err(e) => {
                state_manager.transition_to(ContainerState::Failed {
                    container_id,
                    error: e.to_string(),
                    occurred_at: Instant::now(),
                }).await.map_err(DockerError::State)?;
            }
        }

        result
    }

    async fn get_container_id(&self) -> DockerResult<String> {
        let command = DockerCommand::new("ps")
            .arg("-q")
            .arg("-l");

        let output = self.docker_executor.execute(command).await?;
        if output.success {
            Ok(output.stdout.trim().to_string())
        } else {
            Err(DockerError::State(StateError::ContainerNotFound(
                "コンテナIDの取得に失敗しました".to_string()
            )))
        }
    }

    pub async fn subscribe_to_state_changes(&mut self) -> tokio::sync::mpsc::Receiver<ContainerState> {
        let mut state_manager = self.state_manager.lock().await;
        state_manager.subscribe().await
    }

    pub async fn get_current_state(&self) -> ContainerState {
        let state_manager = self.state_manager.lock().await;
        state_manager.get_current_state().clone()
    }
} 