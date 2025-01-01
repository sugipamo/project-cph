use std::io;
use std::path::StripPrefixError;
use thiserror::Error;

pub const NO_ACTIVE_CONTEST: &str = "アクティブなコンテストがありません。'work'コマンドで設定してください。";

#[derive(Debug, Error)]
pub enum CphError {
    #[error("IOエラー: {0}")]
    Io(#[from] io::Error),

    #[error("YAMLエラー: {0}")]
    Yaml(#[from] serde_yaml::Error),

    #[error("パスエラー: {0}")]
    Path(#[from] StripPrefixError),

    #[error("{0}")]
    Contest(#[from] crate::contest::ContestError),

    #[error("{0}")]
    Message(String),
}

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>; 