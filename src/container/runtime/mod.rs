pub mod builder;
pub mod config;
pub mod container;
pub mod containerd;
pub mod mock;
pub mod orchestrator;

pub use container::Container;
pub use builder::Builder;
pub use container::State;

use async_trait::async_trait;
use anyhow::Result;
use std::path::Path;

#[async_trait]
pub trait Runtime: Send + Sync {
    async fn create(
        &self,
        image: &str,
        command: &[String],
        working_dir: &Path,
        env_vars: &[String],
    ) -> Result<String>;

    async fn start(&self, container_id: &str) -> Result<()>;
    async fn stop(&self, container_id: &str) -> Result<()>;
    async fn remove(&self, container_id: &str) -> Result<()>;
    async fn run(&self, config: &config::Config) -> Result<()>;

    fn box_clone(&self) -> Box<dyn Runtime>;
}

impl Clone for Box<dyn Runtime> {
    fn clone(&self) -> Self {
        self.box_clone()
    }
} 