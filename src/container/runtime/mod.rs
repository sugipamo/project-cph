use std::path::Path;
use anyhow::Result;
use async_trait::async_trait;

/// コンテナランタイムの基本的な操作を定義するトレイト
pub trait Runtime: Clone {
    /// コンテナを作成します
    async fn create(
        &self,
        id: &str,
        image: &str,
        working_dir: &Path,
        args: &[String],
    ) -> Result<()>;

    /// コンテナを開始します
    async fn start(&self, id: &str) -> Result<()>;

    /// コンテナを停止します
    async fn stop(&self, id: &str) -> Result<()>;

    /// コンテナを削除します
    async fn remove(&self, id: &str) -> Result<()>;
}

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