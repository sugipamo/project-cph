use std::fmt;
use crate::error::{Error, ErrorKind, ErrorSeverity};

#[derive(Debug, Clone)]
pub enum ContestErrorKind {
    NotFound,
    Invalid,
    InvalidLanguage,
    InvalidUrl,
    Parse,
    IO,
    Docker,
    Other(String),
}

impl ErrorKind for ContestErrorKind {
    fn severity(&self) -> ErrorSeverity {
        match self {
            Self::NotFound => ErrorSeverity::Warning,
            _ => ErrorSeverity::Error,
        }
    }
}

impl fmt::Display for ContestErrorKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotFound => write!(f, "リソースが見つかりません"),
            Self::Invalid => write!(f, "入力値が不正です"),
            Self::InvalidLanguage => write!(f, "サポートされていない言語です"),
            Self::InvalidUrl => write!(f, "URLの形式が正しくありません"),
            Self::Parse => write!(f, "パースに失敗しました"),
            Self::IO => write!(f, "I/Oエラーが発生しました"),
            Self::Docker => write!(f, "Dockerの操作に失敗しました"),
            Self::Other(s) => write!(f, "{}", s),
        }
    }
}

pub fn contest_error(kind: ContestErrorKind, message: impl Into<String>) -> Error {
    Error::new(kind, message)
        .with_hint("コンテストの操作に失敗しました")
} 