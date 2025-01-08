use async_trait::async_trait;
use std::time::Duration;
use anyhow::Result;
use crate::docker::config::ContainerConfig;

/// Docker操作の基本機能を提供するトレイト
#[async_trait]
pub trait DockerOperations: Send + Sync {
    /// コンテナを作成し、初期化する
    async fn initialize(&mut self, config: ContainerConfig) -> Result<()>;

    /// コンテナを起動する
    async fn start(&mut self) -> Result<()>;

    /// コンテナを停止する
    async fn stop(&mut self) -> Result<()>;

    /// コンテナにコマンドを実行する
    async fn execute(&mut self, command: &str) -> Result<(String, String)>;

    /// コンテナの標準入力にデータを書き込む
    async fn write(&mut self, input: &str) -> Result<()>;

    /// コンテナの標準出力からデータを読み取る
    async fn read_stdout(&mut self, timeout: Duration) -> Result<String>;

    /// コンテナの標準エラー出力からデータを読み取る
    async fn read_stderr(&mut self, timeout: Duration) -> Result<String>;
} 