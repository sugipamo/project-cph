use std::path::Path;
use anyhow::Result;
use crate::fs_err;

/// ファイルを削除します
pub fn delete_file(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Ok(());
    }
    if !path.is_file() {
        return Err(fs_err!("無効なパス: {}", path.display()));
    }
    std::fs::remove_file(path)
        .map_err(|e| fs_err!("ファイルの削除に失敗: {}: {}", path.display(), e))
}

/// ディレクトリを削除します
pub fn delete_dir(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Ok(());
    }
    if !path.is_dir() {
        return Err(fs_err!("無効なパス: {}", path.display()));
    }
    std::fs::remove_dir_all(path)
        .map_err(|e| fs_err!("ディレクトリの削除に失敗: {}: {}", path.display(), e))
} 