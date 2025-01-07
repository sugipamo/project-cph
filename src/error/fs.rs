use crate::error::{Error, ErrorKind, ErrorSeverity};
use std::fmt;

pub fn fs_error(kind: FileSystemErrorKind, message: impl Into<String>) -> Error {
    Error::new(kind, message)
}

pub fn io_err(error: std::io::Error, message: impl Into<String>) -> Error {
    Error::new(
        FileSystemErrorKind::IO,
        format!("{}: {}", message.into(), error)
    ).with_hint("ファイル操作に失敗しました")
}

pub fn not_found_err(path: impl Into<String>) -> Error {
    Error::new(
        FileSystemErrorKind::NotFound,
        format!("ファイルが見つかりません: {}", path.into())
    ).with_hint("ファイルの存在を確認してください")
}

pub fn permission_err(path: impl Into<String>) -> Error {
    Error::new(
        FileSystemErrorKind::Permission,
        format!("アクセス権限がありません: {}", path.into())
    ).with_hint("ファイルのアクセス権限を確認してください")
}

pub fn transaction_err(error: std::io::Error, message: impl Into<String>) -> Error {
    Error::new(
        FileSystemErrorKind::Validation,
        format!("{}: {}", message.into(), error)
    ).with_hint("トランザクションの実行に失敗しました")
}

pub fn path_err(path: impl Into<String>) -> Error {
    Error::new(
        FileSystemErrorKind::Validation,
        format!("無効なパス: {}", path.into())
    ).with_hint("パスの形式を確認してください")
}

pub fn fs_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::fs(
        FileSystemErrorKind::Other(error.into()),
        message
    )
}

#[derive(Debug, Clone)]
pub enum FileSystemErrorKind {
    IO,
    NotFound,
    Permission,
    Validation,
    InvalidPath,
    Other(String),
}

impl ErrorKind for FileSystemErrorKind {
    fn severity(&self) -> ErrorSeverity {
        match self {
            Self::IO | Self::Permission => ErrorSeverity::Fatal,
            Self::NotFound | Self::InvalidPath => ErrorSeverity::Warning,
            _ => ErrorSeverity::Error,
        }
    }
}

impl fmt::Display for FileSystemErrorKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::IO => write!(f, "IOエラー"),
            Self::NotFound => write!(f, "ファイルが見つかりません"),
            Self::Permission => write!(f, "権限がありません"),
            Self::Validation => write!(f, "検証エラー"),
            Self::InvalidPath => write!(f, "無効なパスです"),
            Self::Other(s) => write!(f, "{}", s),
        }
    }
} 