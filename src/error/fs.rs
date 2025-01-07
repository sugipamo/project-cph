use std::path::Path;
use anyhow::Error;

/// ファイルが見つからない場合のエラーを作成します
pub fn not_found_error<P: AsRef<Path>>(path: P) -> Error {
    Error::msg(format!("ファイルが見つかりません: {}", path.as_ref().display()))
}

/// I/Oエラーを作成します
pub fn io_error<P: AsRef<Path>>(error: std::io::Error, path: P) -> Error {
    Error::new(error).context(format!("I/Oエラー: {}", path.as_ref().display()))
}

/// アクセス権限エラーを作成します
pub fn permission_error<P: AsRef<Path>>(path: P) -> Error {
    Error::msg(format!("権限エラー: {}", path.as_ref().display()))
}

/// パスエラーを作成します
pub fn invalid_path_error<P: AsRef<Path>>(path: P) -> Error {
    Error::msg(format!("無効なパス: {}", path.as_ref().display()))
}

/// トランザクションエラーを作成します
pub fn transaction_error(message: impl Into<String>) -> Error {
    Error::msg(format!("トランザクションエラー: {}", message.into()))
}

/// バックアップエラーを作成します
pub fn backup_error(message: impl Into<String>) -> Error {
    Error::msg(format!("バックアップエラー: {}", message.into()))
}

/// 検証エラーを作成します
pub fn validation_error(message: impl Into<String>) -> Error {
    Error::msg(format!("バリデーションエラー: {}", message.into()))
}

/// その他のファイルシステムエラーを作成します
pub fn fs_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_not_found_error() {
        let path = PathBuf::from("/test/path");
        let error = not_found_error(&path);
        assert!(error.to_string().contains("ファイルが見つかりません"));
        assert!(error.to_string().contains("/test/path"));
    }

    #[test]
    fn test_io_error() {
        let path = PathBuf::from("/test/path");
        let io_err = std::io::Error::new(std::io::ErrorKind::Other, "test error");
        let error = io_error(io_err, &path);
        assert!(error.to_string().contains("I/Oエラー"));
        assert!(error.to_string().contains("/test/path"));
    }
} 