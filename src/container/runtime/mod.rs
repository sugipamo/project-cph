pub mod builder;
pub mod config;
pub mod container;
pub mod containerd;
pub mod mock;

pub use container::Container;
pub use builder::ContainerBuilder;

use async_trait::async_trait;
use anyhow::Result;
use std::path::Path;

#[async_trait]
pub trait Runtime: Send + Sync {
    async fn run(&self, config: &self::config::Config) -> Result<()>;
    
    async fn create(
        &self,
        image: &str,
        command: &[String],
        working_dir: &Path,
        env_vars: &[String]
    ) -> Result<String> {
        let _ = (image, command, working_dir, env_vars);
        unimplemented!("create is not implemented for this runtime")
    }
    
    async fn start(&self, container_id: &str) -> Result<()> {
        let _ = container_id;
        unimplemented!("start is not implemented for this runtime")
    }
    
    async fn stop(&self, container_id: &str) -> Result<()> {
        let _ = container_id;
        unimplemented!("stop is not implemented for this runtime")
    }
    
    async fn remove(&self, container_id: &str) -> Result<()> {
        let _ = container_id;
        unimplemented!("remove is not implemented for this runtime")
    }
    
    fn box_clone(&self) -> Box<dyn Runtime>;
}

impl Clone for Box<dyn Runtime> {
    fn clone(&self) -> Self {
        self.box_clone()
    }
} 