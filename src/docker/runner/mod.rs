use std::sync::Arc;
use std::time::Duration;

mod command;
mod container;
mod io;

pub use command::{DockerCommandLayer, DefaultDockerExecutor};
pub use container::{ContainerConfig, ContainerLifecycle};
pub use io::ContainerIO;

use crate::docker::error::DockerResult;
use crate::docker::traits::DockerRunner as DockerRunnerTrait;

pub struct DockerRunner {
    container: ContainerLifecycle,
    io: Option<ContainerIO>,
    timeout: Duration,
}

impl DockerRunner {
    pub fn new(docker: Arc<DockerCommandLayer>, config: ContainerConfig, timeout: Duration) -> Self {
        Self {
            container: ContainerLifecycle::new(docker.clone(), config),
            io: None,
            timeout,
        }
    }

    async fn ensure_image(&mut self) -> DockerResult<()> {
        if !self.container.check_image().await? {
            self.container.pull_image().await?;
        }
        Ok(())
    }

    fn setup_io(&mut self, container_id: String, docker: Arc<DockerCommandLayer>) {
        self.io = Some(ContainerIO::new(docker, container_id));
    }
}

#[async_trait::async_trait]
impl DockerRunnerTrait for DockerRunner {
    async fn initialize(&mut self, cmd: Vec<String>) -> DockerResult<()> {
        // イメージの確認と取得
        self.ensure_image().await?;

        // コンテナの作成と起動
        self.container.create(cmd).await?;
        self.container.start().await?;

        // I/Oの設定
        if let Some(container_id) = self.container.get_container_id() {
            let docker = Arc::new(DockerCommandLayer::new(
                Box::new(DefaultDockerExecutor::new())
            ));
            self.setup_io(container_id.to_string(), docker);
        }

        Ok(())
    }

    async fn write(&self, input: &str) -> DockerResult<()> {
        if let Some(io) = &self.io {
            io.write(input).await
        } else {
            Err(crate::docker::error::DockerError::IO(
                "I/Oが初期化されていません".to_string(),
            ))
        }
    }

    async fn read_stdout(&self) -> DockerResult<String> {
        if let Some(io) = &self.io {
            io.read_stdout(self.timeout).await
        } else {
            Err(crate::docker::error::DockerError::IO(
                "I/Oが初期化されていません".to_string(),
            ))
        }
    }

    async fn read_stderr(&self) -> DockerResult<String> {
        if let Some(io) = &self.io {
            io.read_stderr(self.timeout).await
        } else {
            Err(crate::docker::error::DockerError::IO(
                "I/Oが初期化されていません".to_string(),
            ))
        }
    }

    async fn stop(&mut self) -> DockerResult<()> {
        self.container.stop().await
    }
} 