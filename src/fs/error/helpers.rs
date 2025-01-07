use std::path::Path;
use anyhow::Error;

/// ファイルが見つからない場合のエラーを作成します
pub fn create_not_found_error<P: AsRef<Path>>(path: P) -> Error {
    Error::msg(format!("ファイルが見つかりません: {}", path.as_ref().display()))
}

/// I/Oエラーを作成します
pub fn create_io_error<P: AsRef<Path>>(error: std::io::Error, path: P) -> Error {
    Error::new(error).context(format!("I/Oエラー: {}", path.as_ref().display()))
}

/// アクセス権限エラーを作成します
pub fn create_permission_error<P: AsRef<Path>>(path: P) -> Error {
    Error::msg(format!("権限エラー: {}", path.as_ref().display()))
}

/// パスエラーを作成します
pub fn create_invalid_path_error<P: AsRef<Path>>(path: P) -> Error {
    Error::msg(format!("無効なパス: {}", path.as_ref().display()))
}

/// トランザクションエラーを作成します
pub fn create_transaction_error(message: impl Into<String>) -> Error {
    Error::msg(format!("トランザクションエラー: {}", message.into()))
}

/// バックアップエラーを作成します
pub fn create_backup_error(message: impl Into<String>) -> Error {
    Error::msg(format!("バックアップエラー: {}", message.into()))
}

/// 検証エラーを作成します
pub fn create_validation_error(message: impl Into<String>) -> Error {
    Error::msg(format!("バリデーションエラー: {}", message.into()))
}

/// その他のファイルシステムエラーを作成します
pub fn create_other_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_create_not_found_error() {
        let path = PathBuf::from("test.txt");
        let error = create_not_found_error(&path);
        assert!(error.to_string().contains("test.txt"));
        assert!(error.to_string().contains("ファイルが見つかりません"));
    }

    #[test]
    fn test_create_io_error() {
        use std::io::{Error as IoError, ErrorKind};
        let io_error = IoError::new(ErrorKind::Other, "test error");
        let error = create_io_error(io_error, "test.txt");
        assert!(error.to_string().contains("test.txt"));
        assert!(error.to_string().contains("I/Oエラー"));
    }

    #[test]
    fn test_create_permission_error() {
        let path = PathBuf::from("test.txt");
        let error = create_permission_error(&path);
        assert!(error.to_string().contains("test.txt"));
        assert!(error.to_string().contains("権限エラー"));
    }

    #[test]
    fn test_create_invalid_path_error() {
        let path = PathBuf::from("invalid/path");
        let error = create_invalid_path_error(&path);
        assert!(error.to_string().contains("invalid/path"));
        assert!(error.to_string().contains("無効なパス"));
    }

    #[test]
    fn test_create_transaction_error() {
        let error = create_transaction_error("test error");
        assert!(error.to_string().contains("トランザクションエラー"));
    }

    #[test]
    fn test_create_backup_error() {
        let error = create_backup_error("test error");
        assert!(error.to_string().contains("バックアップエラー"));
    }

    #[test]
    fn test_create_validation_error() {
        let error = create_validation_error("test error");
        assert!(error.to_string().contains("バリデーションエラー"));
    }

    #[test]
    fn test_create_other_error() {
        let error = create_other_error("test error");
        assert!(error.to_string().contains("test error"));
    }
} 