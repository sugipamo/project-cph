use std::path::PathBuf;
use std::error::Error as StdError;
use thiserror::Error;

/// コンテスト操作に関するエラー
#[derive(Error, Debug)]
pub enum ContestError {
    #[error("設定エラー: {message}")]
    Config { 
        message: String,
        source: Option<Box<dyn StdError + Send + Sync>>
    },

    #[error("ファイルシステムエラー: {message}, パス: {path:?}")]
    FileSystem {
        message: String,
        source: std::io::Error,
        path: PathBuf
    },

    #[error("検証エラー: {message}")]
    Validation {
        message: String
    },

    #[error("バックアップエラー: {message}, パス: {path:?}")]
    Backup {
        message: String,
        path: PathBuf,
        source: Option<Box<dyn StdError + Send + Sync>>
    },

    #[error("トランザクションエラー: {message}")]
    Transaction {
        message: String,
        context: ErrorContext
    }
}

impl From<std::io::Error> for ContestError {
    fn from(err: std::io::Error) -> Self {
        ContestError::FileSystem {
            message: err.to_string(),
            source: err,
            path: PathBuf::new()
        }
    }
}

impl From<serde_yaml::Error> for ContestError {
    fn from(err: serde_yaml::Error) -> Self {
        ContestError::Config {
            message: err.to_string(),
            source: Some(Box::new(err))
        }
    }
}

impl From<String> for ContestError {
    fn from(message: String) -> Self {
        ContestError::Validation {
            message
        }
    }
}

/// エラーのコンテキスト情報
#[derive(Debug, Clone)]
pub struct ErrorContext {
    pub operation: String,
    pub location: String,
    pub details: std::collections::HashMap<String, String>,
}

impl ErrorContext {
    pub fn new(operation: impl Into<String>, location: impl Into<String>) -> Self {
        Self {
            operation: operation.into(),
            location: location.into(),
            details: std::collections::HashMap::new(),
        }
    }

    pub fn add_detail(&mut self, key: impl Into<String>, value: impl Into<String>) -> &mut Self {
        self.details.insert(key.into(), value.into());
        self
    }
}

/// Result型のエイリアス
pub type Result<T> = std::result::Result<T, ContestError>; 