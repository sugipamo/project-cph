use std::path::Path;
use anyhow::Result;
use async_trait::async_trait;
use cph::container::runtime::Runtime;

#[derive(Clone)]
pub struct MockRuntime {
    container_id: String,
}

impl MockRuntime {
    pub fn new(container_id: String) -> Self {
        Self { container_id }
    }
}

#[async_trait]
impl Runtime for MockRuntime {
    async fn create(
        &self,
        _image: &str,
        _command: &[String],
        _working_dir: &Path,
        _env_vars: &[String],
    ) -> Result<String> {
        Ok(self.container_id.clone())
    }

    async fn start(&self, _container_id: &str) -> Result<()> {
        Ok(())
    }

    async fn stop(&self, _container_id: &str) -> Result<()> {
        Ok(())
    }

    async fn remove(&self, _container_id: &str) -> Result<()> {
        Ok(())
    }
} 