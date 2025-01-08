use async_trait::async_trait;
use anyhow::Result;

/// コンテナのライフサイクルを管理するトレイト
#[async_trait]
pub trait ContainerManager: Send + Sync {
    /// コンテナを作成する
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> Result<()>;
    
    /// コンテナを起動する
    async fn start_container(&mut self) -> Result<()>;
    
    /// コンテナを停止する
    async fn stop_container(&mut self) -> Result<()>;
    
    /// コンテナIDを取得する
    async fn get_container_id(&self) -> Result<String>;
    
    /// 終了コードを取得する
    async fn get_exit_code(&self) -> Result<i32>;
    
    /// イメージの存在確認
    async fn check_image(&self, image: &str) -> Result<bool>;
    
    /// イメージのプル
    async fn pull_image(&self, image: &str) -> Result<()>;
} 