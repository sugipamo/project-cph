use std::path::PathBuf;
use async_trait::async_trait;
use anyhow::Result;

/// コンテナの実行環境を定義するトレイト
#[async_trait]
pub trait ContainerRuntime: Send + Sync {
    /// コンテナを作成します
    ///
    /// # Arguments
    /// * `image` - 使用するイメージ名
    /// * `command` - 実行するコマンド
    /// * `working_dir` - 作業ディレクトリ
    /// * `env_vars` - 環境変数
    ///
    /// # Returns
    /// * `Result<String>` - 作成されたコンテナのID
    async fn create(
        &self,
        image: &str,
        command: &[String],
        working_dir: &PathBuf,
        env_vars: &[String],
    ) -> Result<String>;

    /// コンテナを起動します
    ///
    /// # Arguments
    /// * `container_id` - コンテナID
    async fn start(&self, container_id: &str) -> Result<()>;

    /// コンテナを停止します
    ///
    /// # Arguments
    /// * `container_id` - コンテナID
    async fn stop(&self, container_id: &str) -> Result<()>;

    /// コンテナを削除します
    ///
    /// # Arguments
    /// * `container_id` - コンテナID
    async fn remove(&self, container_id: &str) -> Result<()>;

    /// コンテナ内でコマンドを実行します
    ///
    /// # Arguments
    /// * `container_id` - コンテナID
    /// * `command` - 実行するコマンド
    ///
    /// # Returns
    /// * `Result<(String, String)>` - (標準出力, 標準エラー出力)
    async fn execute(&self, container_id: &str, command: &str) -> Result<(String, String)>;

    /// コンテナの状態を確認します
    ///
    /// # Arguments
    /// * `container_id` - コンテナID
    ///
    /// # Returns
    /// * `Result<bool>` - コンテナが実行中かどうか
    async fn is_running(&self, container_id: &str) -> Result<bool>;
} 