use std::path::Path;
use anyhow::Result;
use async_trait::async_trait;

/// コンテナランタイムの基本的な操作を定義するトレイト
#[async_trait]
pub trait Runtime: Clone + Send + Sync + 'static {
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
}

pub mod config;
pub mod container;
pub mod containerd;

pub use container::Container; 