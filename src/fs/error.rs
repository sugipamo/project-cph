use std::path::Path;
use anyhow::{anyhow, Error};

/// ファイルシステム操作に関連するエラーを生成する関数群
pub fn not_found_error(path: impl AsRef<Path>) -> Error {
    anyhow!("ファイルが見つかりません: {}", path.as_ref().display())
}

pub fn io_error(error: std::io::Error, path: impl AsRef<Path>) -> Error {
    anyhow!(error).context(format!("パス '{}' でI/O操作に失敗しました", path.as_ref().display()))
}

pub fn permission_error(path: impl AsRef<Path>) -> Error {
    anyhow!("アクセス権限がありません: {}", path.as_ref().display())
}

pub fn invalid_path_error(path: impl AsRef<Path>) -> Error {
    anyhow!("無効なパスです: {}", path.as_ref().display())
}

pub fn transaction_error<E: std::error::Error + Send + Sync + 'static>(
    error: E,
    message: impl Into<String>
) -> Error {
    anyhow!(error).context(format!("トランザクションエラー: {}", message.into()))
}

pub fn backup_error<E: std::error::Error + Send + Sync + 'static>(
    error: E,
    message: impl Into<String>
) -> Error {
    anyhow!(error).context(format!("バックアップエラー: {}", message.into()))
}

pub fn validation_error<E: std::error::Error + Send + Sync + 'static>(
    error: E,
    message: impl Into<String>
) -> Error {
    anyhow!(error).context(format!("バリデーションエラー: {}", message.into()))
} 