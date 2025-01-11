use std::path::PathBuf;
use serde::{Deserialize, Serialize};

/// コンテナの設定を保持する構造体
#[derive(Clone, Debug)]
pub struct Config {
    /// コンテナのID
    pub id: String,
    /// 使用するイメージ
    pub image: String,
    /// 作業ディレクトリ
    pub working_dir: PathBuf,
    /// コマンド引数
    pub args: Vec<String>,
}

impl Config {
    /// 新しい設定を作成します
    pub fn new(id: String, image: String, working_dir: PathBuf, args: Vec<String>) -> Self {
        Self {
            id,
            image,
            working_dir,
            args,
        }
    }
} 