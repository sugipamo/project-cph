use std::path::PathBuf;

/// Dockerコンテナの実行設定
#[derive(Debug, Clone)]
pub struct Config {
    /// コンテナのイメージ名
    pub image: String,
    /// コンテナ内で実行するコマンド
    pub command: Vec<String>,
    /// コンテナ内の作業ディレクトリ
    pub working_dir: PathBuf,
    /// コンテナ内の環境変数
    pub env_vars: Vec<String>,
} 