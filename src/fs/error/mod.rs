use std::path::Path;
use anyhow::{Result, Context, anyhow};

/// ファイルシステム操作に関連するエラーを生成する関数群

pub fn not_found_error(path: impl AsRef<Path>) -> anyhow::Error {
    anyhow!("パスが見つかりません: {}", path.as_ref().display())
}

pub fn io_error(error: std::io::Error, message: impl Into<String>) -> anyhow::Error {
    anyhow!("{}: {}", message.into(), error)
}

pub fn permission_error(path: impl AsRef<Path>) -> anyhow::Error {
    anyhow!("権限がありません: {}", path.as_ref().display())
}

pub fn invalid_path_error(path: impl AsRef<Path>) -> anyhow::Error {
    anyhow!("無効なパスです: {}", path.as_ref().display())
}

pub fn transaction_error(message: impl Into<String>) -> anyhow::Error {
    anyhow!("トランザクションエラー: {}", message.into())
}

pub fn backup_error(message: impl Into<String>) -> anyhow::Error {
    anyhow!("バックアップエラー: {}", message.into())
}

pub fn validation_error(message: impl Into<String>) -> anyhow::Error {
    anyhow!("検証エラー: {}", message.into())
}

/// エラー変換のための拡張トレイト
pub trait ErrorExt<T> {
    fn with_context_path(self, path: impl AsRef<Path>) -> Result<T>;
    fn with_context_io(self, message: impl Into<String>) -> Result<T>;
}

impl<T, E: std::error::Error + Send + Sync + 'static> ErrorExt<T> for std::result::Result<T, E> {
    fn with_context_path(self, path: impl AsRef<Path>) -> Result<T> {
        self.with_context(|| format!("パス: {}", path.as_ref().display()))
    }

    fn with_context_io(self, message: impl Into<String>) -> Result<T> {
        self.with_context(|| message.into())
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
        assert!(err.to_string().contains("/test/path"));
        
        let io_err = std::io::Error::new(std::io::ErrorKind::Other, "test error");
        let err = io_error(io_err, "Test message");
        assert!(err.to_string().contains("Test message"));
        
        let err = permission_error(&path);
        assert!(err.to_string().contains("/test/path"));
        
        let err = invalid_path_error(&path);
        assert!(err.to_string().contains("/test/path"));
        
        let err = transaction_error("Test transaction error");
        assert!(err.to_string().contains("Test transaction error"));
        
        let err = backup_error("Test backup error");
        assert!(err.to_string().contains("Test backup error"));
        
        let err = validation_error("Test validation error");
        assert!(err.to_string().contains("Test validation error"));
    }

    #[test]
    fn test_error_context() {
        let path = PathBuf::from("/test/path");
        let result: std::result::Result<(), std::io::Error> = 
            Err(std::io::Error::new(std::io::ErrorKind::Other, "test error"));
        
        let err = result.with_context_path(&path).unwrap_err();
        assert!(err.to_string().contains("/test/path"));
        
        let err = result.with_context_io("Test IO error").unwrap_err();
        assert!(err.to_string().contains("Test IO error"));
    }
} 