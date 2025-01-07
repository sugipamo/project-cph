use std::path::Path;
use anyhow::{Error, Context as _};

/// ファイルが見つからない場合のエラーを作成します
pub fn create_not_found_error(path: impl AsRef<Path>) -> Error {
    Error::msg(format!("ファイルが見つかりません: {}", path.as_ref().display()))
        .context("ファイルの存在を確認してください")
}

/// I/Oエラーを作成します
pub fn create_io_error(error: std::io::Error, context: impl Into<String>) -> Error {
    error.context(context.into())
        .context("I/O操作に失敗しました")
}

/// アクセス権限エラーを作成します
pub fn create_permission_error(path: impl AsRef<Path>) -> Error {
    Error::msg(format!("アクセス権限がありません: {}", path.as_ref().display()))
        .context("ファイルのアクセス権限を確認してください")
}

/// パスエラーを作成します
pub fn create_invalid_path_error(path: impl AsRef<Path>) -> Error {
    Error::msg(format!("無効なパス: {}", path.as_ref().display()))
        .context("パスの形式を確認してください")
}

/// トランザクションエラーを作成します
pub fn create_transaction_error(error: impl Into<String>, context: impl Into<String>) -> Error {
    Error::msg(format!("{}: {}", context.into(), error.into()))
        .context("トランザクション操作に失敗しました")
}

/// バックアップエラーを作成します
pub fn create_backup_error(error: impl Into<String>, context: impl Into<String>) -> Error {
    Error::msg(format!("{}: {}", context.into(), error.into()))
        .context("バックアップ操作に失敗しました")
}

/// 検証エラーを作成します
pub fn create_validation_error(error: impl Into<String>, context: impl Into<String>) -> Error {
    Error::msg(format!("{}: {}", context.into(), error.into()))
        .context("バリデーションに失敗しました")
}

/// その他のファイルシステムエラーを作成します
pub fn create_other_error(error: impl Into<String>, context: impl Into<String>) -> Error {
    Error::msg(format!("{}: {}", context.into(), error.into()))
        .context("予期しないエラーが発生しました")
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
        let error = create_io_error(io_error, "test operation");
        assert!(error.to_string().contains("test operation"));
        assert!(error.to_string().contains("I/O操作に失敗しました"));
    }

    #[test]
    fn test_create_permission_error() {
        let path = PathBuf::from("test.txt");
        let error = create_permission_error(&path);
        assert!(error.to_string().contains("test.txt"));
        assert!(error.to_string().contains("アクセス権限がありません"));
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
        let error = create_transaction_error("test error", "test operation");
        assert!(error.to_string().contains("test operation"));
        assert!(error.to_string().contains("トランザクション操作に失敗しました"));
    }

    #[test]
    fn test_create_backup_error() {
        let error = create_backup_error("test error", "test operation");
        assert!(error.to_string().contains("test operation"));
        assert!(error.to_string().contains("バックアップ操作に失敗しました"));
    }

    #[test]
    fn test_create_validation_error() {
        let error = create_validation_error("test error", "test operation");
        assert!(error.to_string().contains("test operation"));
        assert!(error.to_string().contains("バリデーションに失敗しました"));
    }

    #[test]
    fn test_create_other_error() {
        let error = create_other_error("test error", "test operation");
        assert!(error.to_string().contains("test operation"));
        assert!(error.to_string().contains("予期しないエラーが発生しました"));
    }
} 