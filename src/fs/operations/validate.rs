use std::path::Path;
use anyhow::{Result, anyhow};
use crate::message::fs as fs_message;

/// パスが存在することを確認します
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - パスが存在しない場合
pub fn exists(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Err(anyhow!(fs_message::error("file_not_found", path.display())));
    }
    Ok(())
}

/// パスが有効なパスであることを確認します
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - パスが無効な場合
pub fn is_valid_path(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if path.to_str().is_none() {
        return Err(anyhow!(fs_message::error("invalid_path", path.display())));
    }
    Ok(())
}

/// パスが有効なファイル名であることを確認します
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - ファイル名が無効な場合
pub fn is_valid_filename(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if path.file_name().is_none() {
        return Err(anyhow!(fs_message::error("invalid_path", path.display())));
    }
    Ok(())
} 