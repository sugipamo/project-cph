use std::path::Path;
use anyhow::{Result, Context, anyhow};

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

impl<T, E> ErrorExt<T> for std::result::Result<T, E>
where
    E: std::error::Error + Send + Sync + 'static,
{
    fn with_context_path(self, path: impl AsRef<Path>) -> Result<T> {
        self.with_context(|| format!("パス操作エラー: {}", path.as_ref().display()))
    }

    fn with_context_io(self, message: impl Into<String>) -> Result<T> {
        self.with_context(|| format!("I/Oエラー: {}", message.into()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_error_creation() {
        let path = PathBuf::from("/test/path");
        
        let err = not_found_error(&path);
        assert!(err.to_string().contains("NotFound"));
        assert!(err.to_string().contains("/test/path"));
        
        let io_err = std::io::Error::new(std::io::ErrorKind::Other, "test error");
        let err = io_error(io_err, "Test message");
        assert!(err.to_string().contains("IoError"));
        assert!(err.to_string().contains("Test message"));
        
        let err = permission_error(&path);
        assert!(err.to_string().contains("PermissionDenied"));
        assert!(err.to_string().contains("/test/path"));
        
        let err = invalid_path_error(&path);
        assert!(err.to_string().contains("InvalidPath"));
        assert!(err.to_string().contains("/test/path"));
        
        let err = transaction_error("Test transaction error");
        assert!(err.to_string().contains("TransactionError"));
        assert!(err.to_string().contains("Test transaction error"));
        
        let err = backup_error("Test backup error");
        assert!(err.to_string().contains("BackupError"));
        assert!(err.to_string().contains("Test backup error"));
        
        let err = validation_error("Test validation error");
        assert!(err.to_string().contains("ValidationError"));
        assert!(err.to_string().contains("Test validation error"));
    }

    #[test]
    fn test_error_context() {
        let path = PathBuf::from("/test/path");
        let result: Result<()> = Err(anyhow!("test error"));
        
        let err = result.with_context_path(&path);
        assert!(err.is_err());
        assert!(err.unwrap_err().to_string().contains("/test/path"));
        
        let result: Result<()> = Err(anyhow!("test error"));
        let err = result.with_context_io("Test message");
        assert!(err.is_err());
        assert!(err.unwrap_err().to_string().contains("Test message"));
    }
} 