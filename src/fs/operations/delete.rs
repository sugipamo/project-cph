use crate::fs::error::{invalid_path_error, ErrorExt};
use anyhow::Result;
use std::path::Path;

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
        .with_context_io(format!("ファイルの削除に失敗: {}", path.display()))
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
        .with_context_io(format!("ディレクトリの削除に失敗: {}", path.display()))
} 