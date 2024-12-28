mod container;
mod io;

use std::sync::Arc;
use tokio::sync::Mutex;
use std::path::Path;
use bollard::Docker;

use crate::docker::config::RunnerConfig;
use crate::docker::state::RunnerState;
use crate::docker::error::{DockerError, Result};

pub struct DockerRunner {
    docker: Docker,
    container_id: String,
    state: Arc<Mutex<RunnerState>>,
    stdout_buffer: Arc<Mutex<Vec<String>>>,
    stderr_buffer: Arc<Mutex<Vec<String>>>,
    stdin_tx: Option<tokio::sync::mpsc::Sender<String>>,
    config: RunnerConfig,
    language: String,
}

impl DockerRunner {
    pub async fn new<P: AsRef<Path>>(config_path: P, language: &str) -> Result<Self> {
        let config = RunnerConfig::load(config_path)?;
        config.validate_language(language)?;

        let docker = Docker::connect_with_local_defaults()
            .map_err(DockerError::ConnectionError)?;

        Ok(Self {
            docker,
            container_id: String::new(),
            state: Arc::new(Mutex::new(RunnerState::Ready)),
            stdout_buffer: Arc::new(Mutex::new(Vec::new())),
            stderr_buffer: Arc::new(Mutex::new(Vec::new())),
            stdin_tx: None,
            config,
            language: language.to_string(),
        })
    }

    pub async fn get_state(&self) -> Result<RunnerState> {
        Ok(self.state.lock().await.clone())
    }
}

impl Drop for DockerRunner {
    fn drop(&mut self) {
        if !self.container_id.is_empty() {
            let docker = self.docker.clone();
            let container_id = self.container_id.clone();
            tokio::spawn(async move {
                let _ = docker.remove_container(
                    &container_id,
                    Some(bollard::container::RemoveContainerOptions {
                        force: true,
                        ..Default::default()
                    }),
                ).await;
            });
        }
    }
} 