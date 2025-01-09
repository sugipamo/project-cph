use async_trait::async_trait;
use anyhow::Result;

/// ネットワーク管理を定義するトレイト
#[async_trait]
pub trait NetworkManager: Send + Sync {
    /// コンテナをネットワークに接続します
    ///
    /// # Arguments
    /// * `container_id` - コンテナID
    /// * `network` - ネットワーク名
    async fn connect(&self, container_id: &str, network: &str) -> Result<()>;

    /// コンテナをネットワークから切断します
    ///
    /// # Arguments
    /// * `container_id` - コンテナID
    /// * `network` - ネットワーク名
    async fn disconnect(&self, container_id: &str, network: &str) -> Result<()>;

    /// ネットワークを作成します
    ///
    /// # Arguments
    /// * `name` - ネットワーク名
    async fn create_network(&self, name: &str) -> Result<()>;

    /// ネットワークを削除します
    ///
    /// # Arguments
    /// * `name` - ネットワーク名
    async fn remove_network(&self, name: &str) -> Result<()>;
} 