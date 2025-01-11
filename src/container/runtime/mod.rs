use std::path::PathBuf;
use anyhow::Result;
use async_trait::async_trait;

pub mod config;
pub mod container;

pub use container::Container;

#[async_trait]
pub trait ContainerRuntime: Clone {
    async fn create(
        &self,
        image: &str,
        command: &[String],
        working_dir: &PathBuf,
        env_vars: &[String],
    ) -> Result<String>;

    async fn start(&self, container_id: &str) -> Result<()>;
    async fn stop(&self, container_id: &str) -> Result<()>;
    async fn remove(&self, container_id: &str) -> Result<()>;
} 