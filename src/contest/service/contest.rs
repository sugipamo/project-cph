use std::sync::Arc;
use tokio::sync::Mutex;
use crate::contest::error::{ContestResult, ContestError};
use crate::docker::traits::DockerOperations;
use crate::docker::config::ContainerConfig;

pub struct ContestService {
    docker_operations: Arc<Mutex<dyn DockerOperations>>,
}

impl ContestService {
    pub fn new(docker_operations: Arc<Mutex<dyn DockerOperations>>) -> Self {
        Self {
            docker_operations,
        }
    }

    pub async fn run_contest(&self, source_code: &str) -> ContestResult<String> {
        self.compile_source(source_code).await?;
        self.run_tests().await
    }

    async fn compile_source(&self, source_code: &str) -> ContestResult<()> {
        let mut ops = self.docker_operations.lock().await;
        let config = ContainerConfig::new(
            "rust:latest".to_string(),
            512,
            "/workspace".to_string(),
            "/tmp".to_string(),
        );

        ops.initialize(config).await
            .map_err(|e| ContestError::Docker(e.to_string()))?;
        
        ops.start().await
            .map_err(|e| ContestError::Docker(e.to_string()))?;

        Ok(())
    }

    async fn run_tests(&self) -> ContestResult<String> {
        let mut ops = self.docker_operations.lock().await;
        let (stdout, stderr) = ops.execute("cargo test").await
            .map_err(|e| ContestError::Docker(e.to_string()))?;

        if stderr.is_empty() {
            Ok(stdout)
        } else {
            Err(ContestError::Docker(stderr))
        }
    }
} 