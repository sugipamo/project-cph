use async_trait::async_trait;
use anyhow::Result;

/// イメージ管理を定義するトレイト
#[async_trait]
pub trait ImageManager: Send + Sync {
    /// イメージを取得します
    ///
    /// # Arguments
    /// * `image` - イメージ名
    async fn pull(&self, image: &str) -> Result<()>;

    /// イメージが存在するか確認します
    ///
    /// # Arguments
    /// * `image` - イメージ名
    ///
    /// # Returns
    /// * `Result<bool>` - イメージが存在するかどうか
    async fn exists(&self, image: &str) -> Result<bool>;

    /// イメージを削除します
    ///
    /// # Arguments
    /// * `image` - イメージ名
    async fn remove(&self, image: &str) -> Result<()>;
} 