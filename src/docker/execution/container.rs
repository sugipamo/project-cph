use async_trait::async_trait;
use std::sync::Arc;
use crate::docker::error::{DockerError, DockerResult};
use crate::docker::traits::ContainerManager;
use super::{DockerCommand, DockerCommandExecutor};

pub struct DefaultContainerManager {
    container_id: String,
    memory_limit: u64,
    mount_point: String,
    docker_executor: Arc<dyn DockerCommandExecutor>,
}

impl DefaultContainerManager {
    pub fn new(memory_limit: u64, mount_point: String, executor: Arc<dyn DockerCommandExecutor>) -> Self {
        Self {
            container_id: String::new(),
            memory_limit,
            mount_point,
            docker_executor: executor,
        }
    }

    async fn ensure_container_exists(&self) -> DockerResult<()> {
        if self.container_id.is_empty() {
            return Err(DockerError::Container("コンテナが作成されていません".to_string()));
        }
        Ok(())
    }
}

#[async_trait]
impl ContainerManager for DefaultContainerManager {
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> DockerResult<()> {
        if !self.check_image(image).await? {
            self.pull_image(image).await?;
        }

        let mut command = DockerCommand::new("create")
            .arg("--memory")
            .arg(&format!("{}m", self.memory_limit))
            .arg("-v")
            .arg(&format!("{}:/workspace", self.mount_point))
            .arg("-w")
            .arg(working_dir)
            .arg(image);

        if !cmd.is_empty() {
            command = command.args(cmd);
        }

        let output = self.docker_executor.execute(command).await?;
        if output.success {
            self.container_id = output.stdout.trim().to_string();
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "コンテナの作成に失敗しました: {}",
                output.stderr
            )))
        }
    }

    async fn start_container(&mut self) -> DockerResult<()> {
        self.ensure_container_exists().await?;

        let command = DockerCommand::new("start")
            .arg(&self.container_id);

        let output = self.docker_executor.execute(command).await?;
        if output.success {
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "コンテナの起動に失敗しました: {}",
                output.stderr
            )))
        }
    }

    async fn stop_container(&mut self) -> DockerResult<()> {
        self.ensure_container_exists().await?;

        let command = DockerCommand::new("stop")
            .arg(&self.container_id);

        let output = self.docker_executor.execute(command).await?;
        if output.success {
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "コンテナの停止に失敗しました: {}",
                output.stderr
            )))
        }
    }

    async fn get_container_id(&self) -> DockerResult<String> {
        self.ensure_container_exists().await?;
        Ok(self.container_id.clone())
    }

    async fn get_exit_code(&self) -> DockerResult<i32> {
        self.ensure_container_exists().await?;

        let command = DockerCommand::new("inspect")
            .arg("--format={{.State.ExitCode}}")
            .arg(&self.container_id);

        let output = self.docker_executor.execute(command).await?;
        if output.success {
            output.stdout.trim().parse::<i32>()
                .map_err(|e| DockerError::Container(format!("終了コードの解析に失敗しました: {}", e)))
        } else {
            Err(DockerError::Container(format!(
                "終了コードの取得に失敗しました: {}",
                output.stderr
            )))
        }
    }

    async fn check_image(&self, image: &str) -> DockerResult<bool> {
        let command = DockerCommand::new("image")
            .arg("inspect")
            .arg(image);

        let output = self.docker_executor.execute(command).await?;
        Ok(output.success)
    }

    async fn pull_image(&self, image: &str) -> DockerResult<()> {
        let command = DockerCommand::new("pull")
            .arg(image);

        let output = self.docker_executor.execute(command).await?;
        if output.success {
            Ok(())
        } else {
            Err(DockerError::Container(format!(
                "イメージの取得に失敗しました: {}",
                output.stderr
            )))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;
    use mockall::predicate::*;
    use crate::docker::test_helpers::MockDockerCommandExecutor;

    #[tokio::test]
    async fn test_container_creation() {
        let mut mock_executor = MockDockerCommandExecutor::new();
        mock_executor.expect_execute()
            .returning(|_| {
                Ok(super::super::CommandOutput::new(
                    true,
                    "container_id".to_string(),
                    String::new(),
                ))
            });

        let executor = Arc::new(mock_executor);
        let mut manager = DefaultContainerManager::new(
            512,
            "/tmp".to_string(),
            executor,
        );

        let result = manager.create_container("test-image", vec![], "/workspace").await;
        assert!(result.is_ok());
    }
} 