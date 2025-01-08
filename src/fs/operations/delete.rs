use std::path::Path;
use anyhow::{Result, anyhow};
use crate::message::fs;
use super::validate::{is_file, is_dir};

/// ファイルを削除します。
/// 
/// # Arguments
/// * `path` - 削除するファイルのパス
/// 
/// # Errors
/// - パスが存在しない場合
/// - パスがファイルでない場合
/// - ファイルの削除に失敗した場合
pub fn remove_file(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    is_file(path)?;
    std::fs::remove_file(path)
        .map_err(|e| anyhow!(fs::error("delete_error", e)))
}

/// ディレクトリを削除します。
/// 
/// # Arguments
/// * `path` - 削除するディレクトリのパス
/// 
/// # Errors
/// - パスが存在しない場合
/// - パスがディレクトリでない場合
/// - ディレクトリの削除に失敗した場合
pub fn remove_dir(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    is_dir(path)?;
    std::fs::remove_dir_all(path)
        .map_err(|e| anyhow!(fs::error("delete_error", e)))
} 