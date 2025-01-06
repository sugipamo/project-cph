use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Mutex;

use crate::docker::error::DockerResult;
use crate::docker::traits::DockerOperations;
use crate::docker::state::{ContainerState, StateManager};
use crate::docker::config::ContainerConfig;

pub struct DockerRunner {
    operations: Arc<Mutex<dyn DockerOperations>>,
    state_manager: Arc<Mutex<StateManager>>,
    timeout: Duration,
}

impl DockerRunner {
    pub fn new(operations: Arc<Mutex<dyn DockerOperations>>, timeout: Duration) -> Self {
        Self {
            operations,
            state_manager: Arc::new(Mutex::new(StateManager::new())),
            timeout,
        }
    }

    pub async fn initialize(&mut self, config: ContainerConfig) -> DockerResult<()> {
        let mut ops = self.operations.lock().await;
        ops.initialize(config).await?;

        let mut state_manager = self.state_manager.lock().await;
        state_manager.transition_to(ContainerState::Created {
            container_id: "temp_id".to_string(), // TODO: 実際のコンテナIDを取得
        }).await?;

        Ok(())
    }

    pub async fn start(&mut self) -> DockerResult<()> {
        let mut ops = self.operations.lock().await;
        ops.start().await?;

        let mut state_manager = self.state_manager.lock().await;
        state_manager.transition_to(ContainerState::Running {
            container_id: "temp_id".to_string(), // TODO: 実際のコンテナIDを取得
            start_time: std::time::Instant::now(),
        }).await?;

        Ok(())
    }

    pub async fn stop(&mut self) -> DockerResult<()> {
        let mut ops = self.operations.lock().await;
        ops.stop().await?;

        let mut state_manager = self.state_manager.lock().await;
        state_manager.transition_to(ContainerState::Stopped {
            container_id: "temp_id".to_string(), // TODO: 実際のコンテナIDを取得
            exit_code: 0, // TODO: 実際の終了コードを取得
            execution_time: Duration::from_secs(0), // TODO: 実際の実行時間を計算
        }).await?;

        Ok(())
    }

    pub async fn execute(&mut self, command: &str) -> DockerResult<(String, String)> {
        let mut ops = self.operations.lock().await;
        ops.execute(command).await
    }

    pub async fn write(&mut self, input: &str) -> DockerResult<()> {
        let mut ops = self.operations.lock().await;
        ops.write(input).await
    }

    pub async fn read_stdout(&mut self) -> DockerResult<String> {
        let mut ops = self.operations.lock().await;
        ops.read_stdout(self.timeout).await
    }

    pub async fn read_stderr(&mut self) -> DockerResult<String> {
        let mut ops = self.operations.lock().await;
        ops.read_stderr(self.timeout).await
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