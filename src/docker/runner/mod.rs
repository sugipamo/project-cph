use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Mutex;
use tokio::time::timeout;

use crate::docker::error::{DockerError, DockerResult};
use crate::docker::state::container::{ContainerState, ContainerStateManager};
use crate::docker::config::ContainerConfig;
use crate::docker::executor::{DockerCommand, DockerCommandExecutor};
use crate::docker::traits::ContainerManager;

pub struct DockerRunner {
    container_manager: Arc<Mutex<dyn ContainerManager>>,
    state_manager: Arc<ContainerStateManager>,
    timeout: Duration,
    docker_executor: Arc<dyn DockerCommandExecutor>,
}

impl DockerRunner {
    pub fn new(
        container_manager: Arc<Mutex<dyn ContainerManager>>,
        docker_executor: Arc<dyn DockerCommandExecutor>,
        timeout: Duration
    ) -> Self {
        Self {
            container_manager,
            state_manager: Arc::new(ContainerStateManager::new()),
            timeout,
            docker_executor,
        }
    }

    pub async fn initialize(&mut self, config: ContainerConfig) -> DockerResult<()> {
        let mut manager = self.container_manager.lock().await;
        manager.create_container(&config.image, vec![], &config.working_dir).await?;

        let container_id = manager.get_container_id().await?;
        self.state_manager.set_container_id(container_id.clone()).await;
        
        self.state_manager.create_container(container_id)
            .await
            .map_err(DockerError::State)
    }

    pub async fn start(&mut self) -> DockerResult<()> {
        let container_id = {
            let manager = self.container_manager.lock().await;
            manager.get_container_id().await?
        };

        {
            let mut manager = self.container_manager.lock().await;
            manager.start_container().await?;
        }

        self.state_manager.start_container(container_id)
            .await
            .map_err(DockerError::State)
    }

    pub async fn stop(&mut self) -> DockerResult<()> {
        let container_id = {
            let manager = self.container_manager.lock().await;
            manager.get_container_id().await?
        };

        let exit_code = {
            let mut manager = self.container_manager.lock().await;
            manager.stop_container().await?;
            manager.get_exit_code().await?
        };

        self.state_manager.stop_container(container_id, exit_code)
            .await
            .map_err(DockerError::State)
    }

    pub async fn execute(&mut self, command: &str) -> DockerResult<(String, String)> {
        let container_id = {
            let manager = self.container_manager.lock().await;
            manager.get_container_id().await?
        };

        // コマンド実行状態に遷移
        self.state_manager.execute_command(container_id.clone(), command.to_string())
            .await
            .map_err(DockerError::State)?;

        // タイムアウト付きでコマンドを実行
        let command = DockerCommand::new("exec")
            .arg("-i")
            .arg(&container_id)
            .arg("sh")
            .arg("-c")
            .arg(command);

        let result = timeout(self.timeout, self.docker_executor.execute(command)).await;

        match result {
            Ok(cmd_result) => {
                match cmd_result {
                    Ok(output) => {
                        self.state_manager.start_container(container_id)
                            .await
                            .map_err(DockerError::State)?;
                        Ok((output.stdout, output.stderr))
                    }
                    Err(e) => {
                        self.state_manager.fail_container(
                            container_id,
                            e.to_string(),
                        ).await.map_err(DockerError::State)?;
                        Err(e)
                    }
                }
            }
            Err(_) => {
                let error = format!("コマンドの実行がタイムアウトしました（{}秒）", self.timeout.as_secs());
                self.state_manager.fail_container(container_id, error.clone())
                    .await
                    .map_err(DockerError::State)?;
                Err(DockerError::Command("コマンドの実行がタイムアウトしました".to_string()))
            }
        }
    }

    pub async fn subscribe_to_state_changes(&self) -> tokio::sync::mpsc::Receiver<ContainerState> {
        self.state_manager.subscribe().await
    }

    pub async fn get_current_state(&self) -> ContainerState {
        self.state_manager.get_current_state().await
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::docker::executor::CommandOutput;
    use mockall::mock;
    use tokio::time::sleep;

    mock! {
        DockerExecutor {}
        #[async_trait::async_trait]
        impl DockerCommandExecutor for DockerExecutor {
            async fn execute(&self, command: DockerCommand) -> DockerResult<CommandOutput>;
        }
    }

    mock! {
        ContainerOps {}
        #[async_trait::async_trait]
        impl ContainerManager for ContainerOps {
            async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> DockerResult<()>;
            async fn start_container(&mut self) -> DockerResult<()>;
            async fn stop_container(&mut self) -> DockerResult<()>;
            async fn get_container_id(&self) -> DockerResult<String>;
            async fn get_exit_code(&self) -> DockerResult<i32>;
            async fn check_image(&self, image: &str) -> DockerResult<bool>;
            async fn pull_image(&self, image: &str) -> DockerResult<()>;
        }
    }

    #[tokio::test]
    async fn test_docker_runner_lifecycle() {
        let mut mock_executor = MockDockerExecutor::new();
        mock_executor
            .expect_execute()
            .returning(|_| Ok(CommandOutput {
                success: true,
                stdout: "container_id".to_string(),
                stderr: "".to_string(),
            }));

        let mut mock_ops = MockContainerOps::new();
        mock_ops
            .expect_create_container()
            .returning(|_, _, _| Ok(()));
        mock_ops
            .expect_get_container_id()
            .returning(|| Ok("test_container".to_string()));
        mock_ops
            .expect_start_container()
            .returning(|| Ok(()));
        mock_ops
            .expect_stop_container()
            .returning(|| Ok(()));
        mock_ops
            .expect_get_exit_code()
            .returning(|| Ok(0));

        let mut runner = DockerRunner::new(
            Arc::new(Mutex::new(mock_ops)),
            Arc::new(mock_executor),
            Duration::from_secs(30),
        );

        // Test initialization
        let config = ContainerConfig {
            image: "test-image".to_string(),
            memory_limit: 512,
            mount_point: "/tmp".to_string(),
            working_dir: "/workspace".to_string(),
        };
        assert!(runner.initialize(config).await.is_ok());

        // Test state transitions
        let state = runner.get_current_state().await;
        assert!(matches!(state, ContainerState::Created { .. }));

        assert!(runner.start().await.is_ok());
        let state = runner.get_current_state().await;
        assert!(matches!(state, ContainerState::Running { .. }));

        assert!(runner.stop().await.is_ok());
        let state = runner.get_current_state().await;
        assert!(matches!(state, ContainerState::Stopped { .. }));
    }

    #[tokio::test]
    async fn test_command_timeout() {
        let mut mock_executor = MockDockerExecutor::new();
        mock_executor
            .expect_execute()
            .returning(|_| {
                sleep(Duration::from_secs(2));
                Ok(CommandOutput {
                    success: true,
                    stdout: "".to_string(),
                    stderr: "".to_string(),
                })
            });

        let mut mock_ops = MockContainerOps::new();
        mock_ops
            .expect_get_container_id()
            .returning(|| Ok("test_container".to_string()));

        let mut runner = DockerRunner::new(
            Arc::new(Mutex::new(mock_ops)),
            Arc::new(mock_executor),
            Duration::from_secs(1),
        );

        let result = runner.execute("test_command").await;
        assert!(matches!(result, Err(DockerError::Command(_))));

        let state = runner.get_current_state().await;
        assert!(matches!(state, ContainerState::Failed { .. }));
    }

    #[tokio::test]
    async fn test_exit_code() {
        let mut mock_executor = MockDockerExecutor::new();
        mock_executor
            .expect_execute()
            .returning(|_| Ok(CommandOutput {
                success: true,
                stdout: "".to_string(),
                stderr: "".to_string(),
            }));

        let mut mock_ops = MockContainerOps::new();
        mock_ops
            .expect_get_container_id()
            .returning(|| Ok("test_container".to_string()));
        mock_ops
            .expect_stop_container()
            .returning(|| Ok(()));
        mock_ops
            .expect_get_exit_code()
            .returning(|| Ok(137));

        let mut runner = DockerRunner::new(
            Arc::new(Mutex::new(mock_ops)),
            Arc::new(mock_executor),
            Duration::from_secs(30),
        );

        assert!(runner.stop().await.is_ok());
        let state = runner.get_current_state().await;
        if let ContainerState::Stopped { exit_code, .. } = state {
            assert_eq!(exit_code, 137);
        } else {
            panic!("Expected Stopped state");
        }
    }
} 