use std::fmt;
use crate::error::{Error, ErrorKind, ErrorSeverity};

pub fn config_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::config(
        ConfigErrorKind::Other(error.into()),
        message
    )
}

#[derive(Debug, Clone)]
pub enum ConfigErrorKind {
    NotFound,
    InvalidFormat,
    InvalidValue,
    IO,
    Other(String),
}

impl ErrorKind for ConfigErrorKind {
    fn severity(&self) -> ErrorSeverity {
        match self {
            Self::NotFound => ErrorSeverity::Warning,
            Self::IO => ErrorSeverity::Fatal,
            _ => ErrorSeverity::Error,
        }
    }
}

impl fmt::Display for ConfigErrorKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotFound => write!(f, "設定ファイルが見つかりません"),
            Self::InvalidFormat => write!(f, "設定ファイルの形式が不正です"),
            Self::InvalidValue => write!(f, "設定値が不正です"),
            Self::IO => write!(f, "設定ファイルのI/O操作に失敗しました"),
            Self::Other(s) => write!(f, "{}", s),
        }
    }
} 