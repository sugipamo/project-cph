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
use crate::docker::state::RunnerStatus;

pub struct DockerRunner {
    container: ContainerLifecycle,
    io: Option<ContainerIO>,
    timeout: Duration,
    status: RunnerStatus,
}

impl DockerRunner {
    pub fn new(docker: Arc<DockerCommandLayer>, config: ContainerConfig, timeout: Duration) -> Self {
        Self {
            container: ContainerLifecycle::new(docker.clone(), config),
            io: None,
            timeout,
            status: RunnerStatus::Ready,
        }
    }

    pub fn get_status(&self) -> RunnerStatus {
        self.status.clone()
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

    fn update_status(&mut self, new_status: RunnerStatus) -> DockerResult<()> {
        if self.can_transition_to(&new_status) {
            self.status = new_status;
            Ok(())
        } else {
            Err(crate::docker::error::DockerError::State(
                format!("無効な状態遷移: {:?} -> {:?}", self.status, new_status)
            ))
        }
    }

    fn can_transition_to(&self, next: &RunnerStatus) -> bool {
        match (&self.status, next) {
            (RunnerStatus::Ready, RunnerStatus::Running) => true,
            (RunnerStatus::Running, RunnerStatus::Stop) => true,
            (RunnerStatus::Running, RunnerStatus::Error(_)) => true,
            (RunnerStatus::Running, RunnerStatus::Completed) => true,
            (RunnerStatus::Error(_), RunnerStatus::Stop) => true,
            _ => false
        }
    }
}

#[async_trait::async_trait]
impl DockerRunnerTrait for DockerRunner {
    async fn initialize(&mut self, cmd: Vec<String>) -> DockerResult<()> {
        self.update_status(RunnerStatus::Running)?;

        // イメージの確認と取得
        if let Err(e) = self.ensure_image().await {
            self.update_status(RunnerStatus::Error(e.to_string()))?;
            return Err(e);
        }

        // コンテナの作成と起動
        if let Err(e) = self.container.create(cmd).await {
            self.update_status(RunnerStatus::Error(e.to_string()))?;
            return Err(e);
        }

        if let Err(e) = self.container.start().await {
            self.update_status(RunnerStatus::Error(e.to_string()))?;
            return Err(e);
        }

        // I/Oの設定
        if let Some(container_id) = self.container.get_container_id() {
            let docker = Arc::new(DockerCommandLayer::new(
                Box::new(DefaultDockerExecutor::new())
            ));
            self.setup_io(container_id.to_string(), docker);
        }

        Ok(())
    }

    async fn write(&mut self, input: &str) -> DockerResult<()> {
        if let Some(io) = &self.io {
            io.write(input).await
        } else {
            let err = crate::docker::error::DockerError::IO(
                "I/Oが初期化されていません".to_string(),
            );
            self.update_status(RunnerStatus::Error(err.to_string()))?;
            Err(err)
        }
    }

    async fn read_stdout(&mut self) -> DockerResult<String> {
        if let Some(io) = &self.io {
            io.read_stdout(self.timeout).await
        } else {
            let err = crate::docker::error::DockerError::IO(
                "I/Oが初期化されていません".to_string(),
            );
            self.update_status(RunnerStatus::Error(err.to_string()))?;
            Err(err)
        }
    }

    async fn read_stderr(&mut self) -> DockerResult<String> {
        if let Some(io) = &self.io {
            io.read_stderr(self.timeout).await
        } else {
            let err = crate::docker::error::DockerError::IO(
                "I/Oが初期化されていません".to_string(),
            );
            self.update_status(RunnerStatus::Error(err.to_string()))?;
            Err(err)
        }
    }

    async fn stop(&mut self) -> DockerResult<()> {
        if let Err(e) = self.container.stop().await {
            self.update_status(RunnerStatus::Error(e.to_string()))?;
            return Err(e);
        }
        self.update_status(RunnerStatus::Stop)?;
        Ok(())
    }
} 