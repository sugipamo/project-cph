use std::path::Path;
use std::fs;
use anyhow::{Result, anyhow};
use crate::message::fs as fs_message;

/// ファイルを削除します
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - ファイルが存在しない場合
/// - ファイルの削除に失敗した場合
pub fn delete_file(path: impl AsRef<Path>) -> Result<()> {
    fs::remove_file(path.as_ref())
        .map_err(|e| anyhow!(fs_message::error("delete_error", e)))
}

/// ディレクトリを再帰的に削除します
///
/// # Errors
///
/// 以下の場合にエラーを返します：
/// - ディレクトリが存在しない場合
/// - ディレクトリの削除に失敗した場合
pub fn delete_dir_recursive(path: impl AsRef<Path>) -> Result<()> {
    fs::remove_dir_all(path.as_ref())
        .map_err(|e| anyhow!(fs_message::error("delete_error", e)))
} 