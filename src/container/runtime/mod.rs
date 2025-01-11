use std::path::Path;
use anyhow::Result;
use async_trait::async_trait;

/// コンテナランタイムの基本的な操作を定義するトレイト
#[async_trait]
pub trait Runtime: Send + Sync + 'static {
    /// コンテナを作成します
    async fn create(
        &self,
        image: &str,
        command: &[String],
        working_dir: &Path,
        env_vars: &[String],
    ) -> Result<String>;

    /// コンテナを開始します
    async fn start(&self, container_id: &str) -> Result<()>;

    /// コンテナを停止します
    async fn stop(&self, container_id: &str) -> Result<()>;

    /// コンテナを削除します
    async fn remove(&self, container_id: &str) -> Result<()>;

    /// ランタイムのクローンを作成します
    fn box_clone(&self) -> Box<dyn Runtime>;
}

pub mod config;
pub mod container;
pub mod containerd;
pub mod builder;

pub use container::Container;
pub use config::{Config, ResourceLimits};
pub use builder::ContainerBuilder; 