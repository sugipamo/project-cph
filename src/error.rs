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

impl ContestError {
    /// 設定関連のエラーを生成
    pub fn config(message: impl Into<String>) -> Self {
        ContestError::Config(message.into())
    }

    /// ファイルシステム関連のエラーを生成
    pub fn fs(message: impl Into<String>) -> Self {
        ContestError::FileSystem(message.into())
    }

    /// 言語関連のエラーを生成
    pub fn language(message: impl Into<String>) -> Self {
        ContestError::Language(message.into())
    }

    /// サイト関連のエラーを生成
    pub fn site(message: impl Into<String>) -> Self {
        ContestError::Site(message.into())
    }
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

    #[error("{0}")]
    Message(String),
}

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>; 