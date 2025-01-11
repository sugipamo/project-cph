mod builder;
pub mod config;
pub mod container;
pub mod mock;

pub use container::Container;
pub use builder::ContainerBuilder;
pub use config::Config;

use anyhow::Result;
use async_trait::async_trait;

#[async_trait]
pub trait Runtime: Send + Sync + 'static {
    async fn run(&self, config: &Config) -> Result<()>;
    fn box_clone(&self) -> Box<dyn Runtime>;
} 