use async_trait::async_trait;
use std::sync::Arc;
use crate::docker::error::{DockerError, DockerResult};
use crate::docker::traits::ContainerManager;
use crate::docker::executor::{DockerCommand, DockerCommandExecutor};

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
        if !self.container_id.is_empty() {
            return Err(DockerError::Container("コンテナは既に作成されています".to_string()));
        }

        let memory_limit = format!("{}m", self.memory_limit);
        let mount_point = format!("{}:{}", self.mount_point, working_dir);

        let command = DockerCommand::new("create")
            .arg("-i")
            .arg("--rm")
            .arg("-m")
            .arg(&memory_limit)
            .arg("-v")
            .arg(&mount_point)
            .arg("-w")
            .arg(working_dir)
            .arg(image)
            .args(cmd);

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
        if self.container_id.is_empty() {
            return Ok(());
        }

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