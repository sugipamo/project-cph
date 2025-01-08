use async_trait::async_trait;
use std::time::Duration;
use anyhow::Result;
use crate::docker::config::Config;

/// Dockerコンテナの実行操作を提供するトレイト
///
/// このトレイトは、Dockerコンテナの実行に関連する
/// 基本的な操作を定義します。
#[async_trait]
pub trait Operations: Send + Sync {
    /// コンテナを作成し、初期化します
    ///
    /// # Arguments
    /// * `config` - コンテナの実行設定
    ///
    /// # Returns
    /// * `Result<()>` - 初期化結果
    ///
    /// # Errors
    /// * コンテナの作成または初期化に失敗した場合
    async fn initialize(&mut self, config: Config) -> Result<()>;

    /// コンテナを起動します
    ///
    /// # Returns
    /// * `Result<()>` - 起動結果
    ///
    /// # Errors
    /// * コンテナの起動に失敗した場合
    async fn start(&mut self) -> Result<()>;

    /// コンテナを停止します
    ///
    /// # Returns
    /// * `Result<()>` - 停止結果
    ///
    /// # Errors
    /// * コンテナの停止に失敗した場合
    async fn stop(&mut self) -> Result<()>;

    /// コンテナでコマンドを実行します
    ///
    /// # Arguments
    /// * `command` - 実行するコマンド
    ///
    /// # Returns
    /// * `Result<(String, String)>` - (標準出力, 標準エラー出力)
    ///
    /// # Errors
    /// * コマンドの実行に失敗した場合
    async fn execute(&mut self, command: &str) -> Result<(String, String)>;

    /// コンテナの標準入力にデータを書き込みます
    ///
    /// # Arguments
    /// * `input` - 書き込むデータ
    ///
    /// # Returns
    /// * `Result<()>` - 書き込み結果
    ///
    /// # Errors
    /// * データの書き込みに失敗した場合
    async fn write(&mut self, input: &str) -> Result<()>;

    /// コンテナの標準出力からデータを読み取ります
    ///
    /// # Arguments
    /// * `timeout` - 読み取りのタイムアウト時間
    ///
    /// # Returns
    /// * `Result<String>` - 読み取ったデータ
    ///
    /// # Errors
    /// * データの読み取りに失敗した場合
    /// * タイムアウトが発生した場合
    async fn read_stdout(&mut self, timeout: Duration) -> Result<String>;

    /// コンテナの標準エラー出力からデータを読み取ります
    ///
    /// # Arguments
    /// * `timeout` - 読み取りのタイムアウト時間
    ///
    /// # Returns
    /// * `Result<String>` - 読み取ったデータ
    ///
    /// # Errors
    /// * データの読み取りに失敗した場合
    /// * タイムアウトが発生した場合
    async fn read_stderr(&mut self, timeout: Duration) -> Result<String>;
} 