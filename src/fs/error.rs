use std::path::Path;
use anyhow::{Result, Context, anyhow};
use std::error::Error as StdError;

/// エラーメッセージを生成するマクロ
#[macro_export]
macro_rules! fs_error {
    ($kind:ident, $($arg:tt)*) => {
        anyhow!("{}: {}", stringify!($kind), format!($($arg)*))
    };
}

/// パスに関連するエラーメッセージを生成するマクロ
#[macro_export]
macro_rules! fs_path_error {
    ($kind:ident, $path:expr) => {
        anyhow!("{}: {}", stringify!($kind), $path.as_ref().display())
    };
}

/// ファイルシステム操作に関連するエラーを生成する関数群
pub fn not_found_error(path: impl AsRef<Path>) -> anyhow::Error {
    fs_path_error!(NotFound, path)
}

pub fn io_error(error: std::io::Error, message: impl Into<String>) -> anyhow::Error {
    fs_error!(IoError, "{}: {}", message.into(), error)
}

pub fn permission_error(path: impl AsRef<Path>) -> anyhow::Error {
    fs_path_error!(PermissionDenied, path)
}

pub fn invalid_path_error(path: impl AsRef<Path>) -> anyhow::Error {
    fs_path_error!(InvalidPath, path)
}

pub fn transaction_error(message: impl Into<String>) -> anyhow::Error {
    fs_error!(TransactionError, "{}", message.into())
}

pub fn backup_error(message: impl Into<String>) -> anyhow::Error {
    fs_error!(BackupError, "{}", message.into())
}

pub fn validation_error(message: impl Into<String>) -> anyhow::Error {
    fs_error!(ValidationError, "{}", message.into())
}

/// エラー変換のための拡張トレイト
pub trait ErrorExt<T> {
    fn with_context_path(self, path: impl AsRef<Path>) -> Result<T>;
    fn with_context_io(self, message: impl Into<String>) -> Result<T>;
}

impl<T> ErrorExt<T> for Result<T> {
    fn with_context_path(self, path: impl AsRef<Path>) -> Result<T> {
        self.with_context(|| format!("パス操作エラー: {}", path.as_ref().display()))
    }

    fn with_context_io(self, message: impl Into<String>) -> Result<T> {
        self.with_context(|| format!("I/Oエラー: {}", message.into()))
    }
} 