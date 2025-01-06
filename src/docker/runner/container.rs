use std::sync::Arc;
use crate::docker::error::{DockerError, DockerResult};
use crate::docker::runner::command::DockerCommandLayer;

pub struct ContainerConfig {
    pub image: String,
    pub memory_limit: u64,
    pub mount_point: String,
    pub working_dir: String,
}

pub struct ContainerLifecycle {
    docker: Arc<DockerCommandLayer>,
    config: ContainerConfig,
    container_id: Option<String>,
}

impl ContainerLifecycle {
    pub fn new(docker: Arc<DockerCommandLayer>, config: ContainerConfig) -> Self {
        Self {
            docker,
            config,
            container_id: None,
        }
    }

    pub async fn create(&mut self, cmd: Vec<String>) -> DockerResult<()> {
        let mut args = vec![
            "create".to_string(),
            "-i".to_string(),
            "--rm".to_string(),
            "-m".to_string(),
            format!("{}m", self.config.memory_limit),
            "-v".to_string(),
            format!("{}:{}", self.config.mount_point, self.config.working_dir),
            "-w".to_string(),
            self.config.working_dir.clone(),
            self.config.image.clone(),
        ];
        args.extend(cmd);

        let (stdout, _) = self.docker.run_command(args).await?;
        self.container_id = Some(stdout.trim().to_string());
        Ok(())
    }

    pub async fn start(&self) -> DockerResult<()> {
        if let Some(container_id) = &self.container_id {
            let args = vec!["start".to_string(), container_id.clone()];
            self.docker.run_command(args).await?;
            Ok(())
        } else {
            Err(DockerError::Container("コンテナが作成されていません".to_string()))
        }
    }

    pub async fn stop(&self) -> DockerResult<()> {
        if let Some(container_id) = &self.container_id {
            let args = vec!["stop".to_string(), container_id.clone()];
            self.docker.run_command(args).await?;
            Ok(())
        } else {
            Ok(())
        }
    }

    pub async fn check_image(&self) -> DockerResult<bool> {
        let args = vec!["image".to_string(), "inspect".to_string(), self.config.image.clone()];
        let result = self.docker.run_command(args).await;
        Ok(result.is_ok())
    }

    pub async fn pull_image(&self) -> DockerResult<()> {
        let args = vec!["pull".to_string(), self.config.image.clone()];
        self.docker.run_command(args).await?;
        Ok(())
    }

    pub fn get_container_id(&self) -> Option<&str> {
        self.container_id.as_deref()
    }
} 