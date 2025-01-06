use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Mutex;

use crate::docker::error::DockerResult;
use crate::docker::traits::{DockerOperation, DockerCommand, CommandType};
use crate::docker::state::{DockerState, DockerStateManager};

pub struct DockerRunner {
    operation: Arc<dyn DockerOperation>,
    state_manager: Arc<Mutex<DockerStateManager>>,
    timeout: Duration,
}

impl DockerRunner {
    pub fn new(operation: Arc<dyn DockerOperation>, timeout: Duration, runner_id: String) -> Self {
        Self {
            operation,
            state_manager: Arc::new(Mutex::new(DockerStateManager::new(runner_id))),
            timeout,
        }
    }

    pub async fn initialize(&mut self, config: ContainerConfig) -> DockerResult<()> {
        let command = DockerCommand {
            command_type: CommandType::Create,
            args: config.into_args(),
            timeout: Some(self.timeout),
        };

        let output = self.operation.execute(command).await?;
        if output.success {
            let container_id = output.stdout.trim().to_string();
            let mut state_manager = self.state_manager.lock().await;
            
            state_manager.transition_to(DockerState::Created {
                container_id: container_id.clone(),
                created_at: std::time::Instant::now(),
            }).await?;

            Ok(())
        } else {
            let mut state_manager = self.state_manager.lock().await;
            state_manager.transition_to(DockerState::Failed {
                container_id: None,
                error: output.stderr.clone(),
                occurred_at: std::time::Instant::now(),
            }).await?;
            Err(crate::docker::error::DockerError::Initialization(output.stderr))
        }
    }

    pub async fn start(&mut self) -> DockerResult<()> {
        let state_manager = self.state_manager.lock().await;
        let current_state = state_manager.get_current_state().await;
        
        if let DockerState::Created { container_id, .. } = current_state {
            let command = DockerCommand {
                command_type: CommandType::Start,
                args: vec![container_id.clone()],
                timeout: Some(self.timeout),
            };
            
            drop(state_manager); // ロックを解放
            
            let output = self.operation.execute(command).await?;
            if output.success {
                let mut state_manager = self.state_manager.lock().await;
                state_manager.transition_to(DockerState::Running {
                    container_id,
                    start_time: std::time::Instant::now(),
                    memory_usage: None,
                }).await?;
                Ok(())
            } else {
                let mut state_manager = self.state_manager.lock().await;
                state_manager.transition_to(DockerState::Failed {
                    container_id: Some(container_id),
                    error: output.stderr.clone(),
                    occurred_at: std::time::Instant::now(),
                }).await?;
                Err(crate::docker::error::DockerError::Container(output.stderr))
            }
        } else {
            Err(crate::docker::error::DockerError::InvalidState(
                "Container must be in Created state to start".to_string()
            ))
        }
    }

    pub async fn cleanup(&mut self) -> DockerResult<()> {
        let state_manager = self.state_manager.lock().await;
        let current_state = state_manager.get_current_state().await;
        
        if let DockerState::Running { container_id, start_time, .. } = current_state {
            let command = DockerCommand {
                command_type: CommandType::Stop,
                args: vec![container_id.clone()],
                timeout: Some(Duration::from_secs(10)),
            };
            
            drop(state_manager);
            
            let output = self.operation.execute(command).await?;
            self.operation.cleanup().await?;
            
            let mut state_manager = self.state_manager.lock().await;
            state_manager.transition_to(DockerState::Completed {
                container_id,
                exit_code: output.exit_code.unwrap_or(0),
                execution_time: start_time.elapsed(),
                output: output.stdout,
            }).await?;
            
            Ok(())
        } else {
            Ok(())
        }
    }

    pub async fn get_state(&self) -> DockerState {
        let state_manager = self.state_manager.lock().await;
        state_manager.get_current_state().await
    }

    pub async fn subscribe_to_state_changes(&mut self) -> tokio::sync::mpsc::Receiver<crate::docker::state::StateChange> {
        let mut state_manager = self.state_manager.lock().await;
        state_manager.subscribe().await
    }
}

#[derive(Clone)]
pub struct ContainerConfig {
    pub image: String,
    pub memory_limit: u64,
    pub working_dir: String,
    pub mount_point: String,
}

impl ContainerConfig {
    fn into_args(self) -> Vec<String> {
        vec![
            "create".to_string(),
            "-i".to_string(),
            "--rm".to_string(),
            "-m".to_string(),
            format!("{}m", self.memory_limit),
            "-v".to_string(),
            format!("{}:{}", self.mount_point, self.working_dir),
            "-w".to_string(),
            self.working_dir,
            self.image,
        ]
    }
} 