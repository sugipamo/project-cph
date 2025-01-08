use async_trait::async_trait;
use anyhow::Result;

/// Dockerコンテナのランタイム管理を行うトレイト
///
/// このトレイトは、Dockerコンテナのライフサイクル管理に必要な
/// 基本的な操作を定義します。
#[async_trait]
pub trait RuntimeManager: Send + Sync {
    /// コンテナを作成します
    ///
    /// # Arguments
    /// * `image` - 使用するDockerイメージ名
    /// * `cmd` - コンテナで実行するコマンドとその引数
    /// * `working_dir` - コンテナ内の作業ディレクトリ
    ///
    /// # Returns
    /// * `Result<()>` - 作成結果
    ///
    /// # Errors
    /// * コンテナの作成に失敗した場合
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> Result<()>;
    
    /// コンテナを起動します
    ///
    /// # Returns
    /// * `Result<()>` - 起動結果
    ///
    /// # Errors
    /// * コンテナの起動に失敗した場合
    async fn start_container(&mut self) -> Result<()>;
    
    /// コンテナを停止します
    ///
    /// # Returns
    /// * `Result<()>` - 停止結果
    ///
    /// # Errors
    /// * コンテナの停止に失敗した場合
    async fn stop_container(&mut self) -> Result<()>;
    
    /// コンテナIDを取得します
    ///
    /// # Returns
    /// * `Result<String>` - コンテナID
    ///
    /// # Errors
    /// * コンテナIDの取得に失敗した場合
    async fn get_container_id(&self) -> Result<String>;
    
    /// コンテナの終了コードを取得します
    ///
    /// # Returns
    /// * `Result<i32>` - 終了コード
    ///
    /// # Errors
    /// * 終了コードの取得に失敗した場合
    async fn get_exit_code(&self) -> Result<i32>;
    
    /// イメージの存在を確認します
    ///
    /// # Arguments
    /// * `image` - 確認するDockerイメージ名
    ///
    /// # Returns
    /// * `Result<bool>` - イメージが存在する場合はtrue
    ///
    /// # Errors
    /// * イメージの確認に失敗した場合
    async fn check_image(&self, image: &str) -> Result<bool>;
    
    /// イメージをプルします
    ///
    /// # Arguments
    /// * `image` - プルするDockerイメージ名
    ///
    /// # Returns
    /// * `Result<()>` - プル結果
    ///
    /// # Errors
    /// * イメージのプルに失敗した場合
    async fn pull_image(&self, image: &str) -> Result<()>;
} 