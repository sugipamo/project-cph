use std::path::PathBuf;
use std::error::Error as StdError;
use thiserror::Error;
use crate::config::ConfigError;
use crate::docker::DockerError;

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

    #[error("Dockerエラー: {message}")]
    Docker {
        message: String,
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

impl From<ConfigError> for ContestError {
    fn from(err: ConfigError) -> Self {
        ContestError::Config {
            message: err.to_string(),
            source: Some(Box::new(err))
        }
    }
}

impl From<DockerError> for ContestError {
    fn from(err: DockerError) -> Self {
        ContestError::Docker {
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

    pub fn with_hint(mut self, hint: impl Into<String>) -> Self {
        self.details.insert("hint".to_string(), hint.into());
        self
    }

    #[cfg(debug_assertions)]
    pub fn with_stack_trace(mut self) -> Self {
        let backtrace = std::backtrace::Backtrace::capture();
        self.details.insert("stack_trace".to_string(), format!("{:?}", backtrace));
        self
    }

    #[cfg(not(debug_assertions))]
    pub fn with_stack_trace(self) -> Self {
        self
    }
}

pub type Result<T> = std::result::Result<T, ContestError>;

impl ContestError {
    pub fn with_context(self, operation: impl Into<String>, location: impl Into<String>) -> Self {
        match self {
            Self::Config { message, source } => Self::Config {
                message: format!("{} (操作: {}, 場所: {})", message, operation.into(), location.into()),
                source,
            },
            Self::FileSystem { message, source, path } => Self::FileSystem {
                message: format!("{} (操作: {}, 場所: {})", message, operation.into(), location.into()),
                source,
                path,
            },
            Self::Validation { message } => Self::Validation {
                message: format!("{} (操作: {}, 場所: {})", message, operation.into(), location.into()),
            },
            Self::Docker { message, source } => Self::Docker {
                message: format!("{} (操作: {}, 場所: {})", message, operation.into(), location.into()),
                source,
            },
            Self::Transaction { message, context } => Self::Transaction {
                message: format!("{} (操作: {}, 場所: {})", message, operation.into(), location.into()),
                context,
            },
        }
    }

    pub fn add_hint(self, hint: impl Into<String>) -> Self {
        match self {
            Self::Config { message, source } => Self::Config {
                message: format!("{}. ヒント: {}", message, hint.into()),
                source,
            },
            Self::FileSystem { message, source, path } => Self::FileSystem {
                message: format!("{}. ヒント: {}", message, hint.into()),
                source,
                path,
            },
            Self::Validation { message } => Self::Validation {
                message: format!("{}. ヒント: {}", message, hint.into()),
            },
            Self::Docker { message, source } => Self::Docker {
                message: format!("{}. ヒント: {}", message, hint.into()),
                source,
            },
            Self::Transaction { message, context } => Self::Transaction {
                message: format!("{}. ヒント: {}", message, hint.into()),
                context,
            },
        }
    }
}
