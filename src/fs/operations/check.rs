use std::path::Path;
use anyhow::{Result, anyhow};
use crate::message::fs;

/// パスの存在確認と権限チェックを行います
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - パスが存在しない場合
/// - メタデータの取得に失敗した場合
/// - 必要な権限がない場合
pub fn check_path_exists(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Err(anyhow!(fs::error("file_not_found", path.display())));
    }

    let metadata = path.metadata()
        .map_err(|e| anyhow!(fs::error("metadata_error", e)))?;

    if !metadata.permissions().readonly() {
        return Err(anyhow!(fs::error("permission_error", path.display())));
    }

    Ok(())
}

/// ファイルの読み取り権限をチェックします
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - パスが存在しない場合
/// - メタデータの取得に失敗した場合
/// - 読み取り権限がない場合
pub fn check_read_permission(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Err(anyhow!(fs::error("file_not_found", path.display())));
    }

    let metadata = path.metadata()
        .map_err(|e| anyhow!(fs::error("metadata_error", e)))?;

    if !metadata.permissions().readonly() {
        return Err(anyhow!(fs::error("permission_error", path.display())));
    }

    Ok(())
}

/// ファイルの書き込み権限をチェックします
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - パスが存在しない場合
/// - メタデータの取得に失敗した場合
/// - 書き込み権限がない場合
pub fn check_write_permission(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Err(anyhow!(fs::error("file_not_found", path.display())));
    }

    let metadata = path.metadata()
        .map_err(|e| anyhow!(fs::error("metadata_error", e)))?;

    if metadata.permissions().readonly() {
        return Err(anyhow!(fs::error("permission_error", path.display())));
    }

    Ok(())
} 