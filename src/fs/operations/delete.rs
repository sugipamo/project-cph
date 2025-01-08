use std::path::Path;
use anyhow::{Result, Context};
use crate::error::fs::*;

/// ファイルを削除します
pub fn delete_file(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Ok(());
    }
    if !path.is_file() {
        return Err(invalid_path_error(path));
    }
    std::fs::remove_file(path)
        .context(format!("ファイルの削除に失敗: {}", path.display()))
}

/// ディレクトリを削除します
pub fn delete_dir(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Ok(());
    }
    if !path.is_dir() {
        return Err(invalid_path_error(path));
    }
    std::fs::remove_dir_all(path)
        .context(format!("ディレクトリの削除に失敗: {}", path.display()))
} 