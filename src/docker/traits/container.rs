use async_trait::async_trait;
use crate::docker::error::DockerResult;

/// コンテナのライフサイクルを管理するトレイト
#[async_trait]
pub trait ContainerManager: Send + Sync {
    /// コンテナを作成する
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> DockerResult<()>;
    
    /// コンテナを起動する
    async fn start_container(&mut self) -> DockerResult<()>;
    
    /// コンテナを停止する
    async fn stop_container(&mut self) -> DockerResult<()>;
    
    /// コンテナIDを取得する
    async fn get_container_id(&self) -> DockerResult<String>;
    
    /// 終了コードを取得する
    async fn get_exit_code(&self) -> DockerResult<i32>;
    
    /// イメージの存在確認
    async fn check_image(&self, image: &str) -> DockerResult<bool>;
    
    /// イメージのプル
    async fn pull_image(&self, image: &str) -> DockerResult<()>;
} 