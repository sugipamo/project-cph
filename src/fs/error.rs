use std::path::PathBuf;
use crate::error::{Error, fs::FileSystemErrorKind};

pub fn io_err(error: std::io::Error, message: impl Into<String>) -> Error {
    Error::fs(
        FileSystemErrorKind::IO,
        format!("{}: {}", message.into(), error)
    )
}

pub fn not_found_err(path: impl Into<PathBuf>) -> Error {
    Error::fs(
        FileSystemErrorKind::NotFound,
        format!("ファイルが見つかりません: {}", path.into().display())
    )
}

pub fn permission_err(path: impl Into<PathBuf>) -> Error {
    Error::fs(
        FileSystemErrorKind::Permission,
        format!("アクセス権限がありません: {}", path.into().display())
    )
}

pub fn validation_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::fs(
        FileSystemErrorKind::Validation,
        format!("{}: {}", message.into(), error.into())
    )
}

pub fn invalid_path_err(path: impl Into<PathBuf>) -> Error {
    Error::fs(
        FileSystemErrorKind::InvalidPath,
        format!("無効なパス: {}", path.into().display())
    )
} 