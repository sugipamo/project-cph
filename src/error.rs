use std::io;
use std::path::StripPrefixError;
use thiserror::Error;

pub const NO_ACTIVE_CONTEST: &str = "アクティブなコンテストがありません。'work'コマンドで設定してください。";

#[derive(Debug, Error)]
pub enum ContestError {
    #[error("設定エラー: {0}")]
    Config(String),
    
    #[error("ファイルシステムエラー: {0}")]
    FileSystem(String),
    
    #[error("言語エラー: {0}")]
    Language(String),
    
    #[error("サイトエラー: {0}")]
    Site(String),
}

#[derive(Debug, Error)]
pub enum CphError {
    #[error("IOエラー: {0}")]
    Io(#[from] io::Error),

    #[error("YAMLエラー: {0}")]
    Yaml(#[from] serde_yaml::Error),

    #[error("パスエラー: {0}")]
    Path(#[from] StripPrefixError),

    #[error("{0}")]
    Contest(#[from] ContestError),

    #[error("Dockerエラー: {0}")]
    Docker(String),

    #[error("ファイルシステムエラー: {0}")]
    Fs(String),

    #[error("{0}")]
    Message(String),
}

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>; 