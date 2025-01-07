use std::fmt;
use crate::error::{Error, ErrorKind, ErrorSeverity};

pub fn contest_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::new(
        ContestErrorKind::Other(error.into()),
        message
    ).with_hint("コンテストの操作に失敗しました")
}

#[derive(Debug, Clone)]
pub enum ContestErrorKind {
    NotFound,
    InvalidLanguage,
    InvalidTestCase,
    InvalidUrl,
    Parse,
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
            Self::InvalidLanguage => write!(f, "サポートされていない言語です"),
            Self::InvalidTestCase => write!(f, "テストケースが不正です"),
            Self::InvalidUrl => write!(f, "URLの形式が正しくありません"),
            Self::Parse => write!(f, "パースに失敗しました"),
            Self::Other(s) => write!(f, "{}", s),
        }
    }
} 