use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Mutex;

use crate::docker::error::DockerResult;
use crate::docker::traits::{DockerOperation, DockerCommand, CommandType};
use crate::docker::state::{RunnerState, ContainerContext, ExecutionResult};

pub struct DockerRunner {
    operation: Arc<dyn DockerOperation>,
    state: Arc<Mutex<RunnerState>>,
    timeout: Duration,
}

impl DockerRunner {
    pub fn new(operation: Arc<dyn DockerOperation>, timeout: Duration) -> Self {
        Self {
            operation,
            state: Arc::new(Mutex::new(RunnerState::Initial)),
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
            let context = ContainerContext {
                container_id: output.stdout.trim().to_string(),
                start_time: std::time::Instant::now(),
                memory_usage: None,
            };
            let mut state = self.state.lock().await;
            *state = RunnerState::Running(context);
            Ok(())
        } else {
            Err(crate::docker::error::DockerError::Initialization(
                output.stderr
            ))
        }
    }

    pub async fn execute(&mut self, cmd: Vec<String>) -> DockerResult<()> {
        let state = self.state.lock().await;
        if let RunnerState::Running(_) = &*state {
            let command = DockerCommand {
                command_type: CommandType::Execute,
                args: cmd,
                timeout: Some(self.timeout),
            };
            
            self.operation.execute(command).await?;
            self.operation.handle_io().await?;
            Ok(())
        } else {
            Err(crate::docker::error::DockerError::State(
                "コンテナが実行状態ではありません".to_string()
            ))
        }
    }

    pub async fn cleanup(&mut self) -> DockerResult<()> {
        let mut state = self.state.lock().await;
        if let RunnerState::Running(context) = &*state {
            let command = DockerCommand {
                command_type: CommandType::Stop,
                args: vec![context.container_id.clone()],
                timeout: Some(Duration::from_secs(10)),
            };
            
            let output = self.operation.execute(command).await?;
            self.operation.cleanup().await?;
            
            *state = RunnerState::Completed(ExecutionResult {
                exit_code: output.exit_code.unwrap_or(0),
                execution_time: context.start_time.elapsed(),
                output: output.stdout,
            });
            Ok(())
        } else {
            Ok(())
        }
    }

    pub async fn get_state(&self) -> RunnerState {
        self.state.lock().await.clone()
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