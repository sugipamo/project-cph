use std::path::Path;
use anyhow::{Error, anyhow};

/// ファイルが見つからない場合のエラーを作成します
pub fn not_found_error<P: AsRef<Path>>(path: P) -> Error {
    Error::msg("ファイルが見つかりません").context(path.as_ref().display().to_string())
}

/// I/Oエラーを作成します
pub fn io_error<P: AsRef<Path>>(error: std::io::Error, path: P) -> Error {
    anyhow!(error).context(format!("I/Oエラー: {}", path.as_ref().display()))
}

/// アクセス権限エラーを作成します
pub fn permission_error<P: AsRef<Path>>(path: P) -> Error {
    Error::msg("アクセス権限がありません").context(path.as_ref().display().to_string())
}

/// パスエラーを作成します
pub fn invalid_path_error<P: AsRef<Path>>(path: P) -> Error {
    Error::msg("無効なパスです").context(path.as_ref().display().to_string())
}

/// トランザクションエラーを作成します
pub fn transaction_error(message: impl Into<String>) -> Error {
    Error::msg("トランザクションエラー").context(message.into())
}

/// バックアップエラーを作成します
pub fn backup_error(message: impl Into<String>) -> Error {
    Error::msg("バックアップエラー").context(message.into())
}

/// 検証エラーを作成します
pub fn validation_error(message: impl Into<String>) -> Error {
    Error::msg("バリデーションエラー").context(message.into())
}

/// その他のファイルシステムエラーを作成します
pub fn fs_error(message: impl Into<String>) -> Error {
    Error::msg("ファイルシステムエラー").context(message.into())
} 