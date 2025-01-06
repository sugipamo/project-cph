use std::sync::Arc;
use tokio::sync::Mutex;
use crate::config::Config;
use crate::contest::error::{ContestError, ContestResult};
use crate::docker::traits::DockerOperations;

pub struct ContestService {
    config: Config,
    docker_operations: Arc<Mutex<Box<dyn DockerOperations>>>,
}

impl ContestService {
    pub fn new(config: Config, docker_operations: Arc<Mutex<Box<dyn DockerOperations>>>) -> Self {
        Self {
            config,
            docker_operations,
        }
    }

    pub async fn run_contest(&self, source_code: &str) -> ContestResult<String> {
        self.compile_source(source_code).await?;
        self.run_tests().await
    }

    async fn compile_source(&self, _source_code: &str) -> ContestResult<()> {
        // TODO: コンパイル処理の実装
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