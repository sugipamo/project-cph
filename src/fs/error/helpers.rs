use std::path::{Path, PathBuf};
use crate::error::Error;
use super::FileSystemErrorKind;

/// ファイルが見つからない場合のエラーを作成します
pub fn create_not_found_error(path: impl AsRef<Path>) -> Error {
    Error::new(
        FileSystemErrorKind::NotFound,
        format!("ファイルが見つかりません: {}", path.as_ref().display())
    ).with_hint("ファイルまたはディレクトリの存在を確認してください")
}

/// I/Oエラーを作成します
pub fn create_io_error(error: std::io::Error, context: impl Into<String>) -> Error {
    Error::new(
        FileSystemErrorKind::Io,
        format!("{}: {}", context.into(), error)
    ).with_hint("ディスクの空き容量やファイルの状態を確認してください")
}

/// アクセス権限エラーを作成します
pub fn create_permission_error(path: impl AsRef<Path>) -> Error {
    Error::new(
        FileSystemErrorKind::Permission,
        format!("アクセス権限がありません: {}", path.as_ref().display())
    ).with_hint("必要な権限があるか確認してください")
}

/// パスエラーを作成します
pub fn create_invalid_path_error(path: impl AsRef<Path>) -> Error {
    Error::new(
        FileSystemErrorKind::InvalidPath,
        format!("無効なパス: {}", path.as_ref().display())
    ).with_hint("パスの形式が正しいか確認してください")
}

/// トランザクションエラーを作成します
pub fn create_transaction_error(error: impl Into<String>, context: impl Into<String>) -> Error {
    Error::new(
        FileSystemErrorKind::Transaction,
        format!("{}: {}", context.into(), error.into())
    ).with_hint("トランザクションの操作をやり直してください")
}

/// バックアップエラーを作成します
pub fn create_backup_error(error: impl Into<String>, context: impl Into<String>) -> Error {
    Error::new(
        FileSystemErrorKind::Backup,
        format!("{}: {}", context.into(), error.into())
    ).with_hint("バックアップの操作をやり直してください")
}

/// 検証エラーを作成します
pub fn create_validation_error(error: impl Into<String>, context: impl Into<String>) -> Error {
    Error::new(
        FileSystemErrorKind::Validation,
        format!("{}: {}", context.into(), error.into())
    ).with_hint("入力値や状態を確認してください")
}

/// その他のファイルシステムエラーを作成します
pub fn create_other_error(error: impl Into<String>, context: impl Into<String>) -> Error {
    Error::new(
        FileSystemErrorKind::Other(error.into()),
        context.into()
    ).with_hint("操作をやり直すか、システム管理者に連絡してください")
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{Error as IoError, ErrorKind};

    #[test]
    fn test_create_not_found_error() {
        let path = PathBuf::from("test.txt");
        let error = create_not_found_error(&path);
        assert!(matches!(error.kind(), &FileSystemErrorKind::NotFound));
        assert!(error.message().contains("test.txt"));
    }

    #[test]
    fn test_create_io_error() {
        let io_error = IoError::new(ErrorKind::Other, "test error");
        let error = create_io_error(io_error, "test operation");
        assert!(matches!(error.kind(), &FileSystemErrorKind::Io));
        assert!(error.message().contains("test operation"));
    }

    #[test]
    fn test_create_permission_error() {
        let path = PathBuf::from("test.txt");
        let error = create_permission_error(&path);
        assert!(matches!(error.kind(), &FileSystemErrorKind::Permission));
        assert!(error.message().contains("test.txt"));
    }

    #[test]
    fn test_create_invalid_path_error() {
        let path = PathBuf::from("../invalid/path");
        let error = create_invalid_path_error(&path);
        assert!(matches!(error.kind(), &FileSystemErrorKind::InvalidPath));
        assert!(error.message().contains("invalid/path"));
    }

    #[test]
    fn test_create_transaction_error() {
        let error = create_transaction_error("test error", "test operation");
        assert!(matches!(error.kind(), &FileSystemErrorKind::Transaction));
        assert!(error.message().contains("test operation"));
    }

    #[test]
    fn test_create_backup_error() {
        let error = create_backup_error("test error", "test operation");
        assert!(matches!(error.kind(), &FileSystemErrorKind::Backup));
        assert!(error.message().contains("test operation"));
    }

    #[test]
    fn test_create_validation_error() {
        let error = create_validation_error("test error", "test operation");
        assert!(matches!(error.kind(), &FileSystemErrorKind::Validation));
        assert!(error.message().contains("test operation"));
    }

    #[test]
    fn test_create_other_error() {
        let error = create_other_error("test error", "test operation");
        if let FileSystemErrorKind::Other(msg) = error.kind() {
            assert_eq!(msg, "test error");
        } else {
            panic!("Expected Other error kind");
        }
        assert!(error.message().contains("test operation"));
    }
} 