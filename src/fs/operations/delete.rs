use std::path::Path;
use anyhow::{Result, anyhow};

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
    if !path.exists() {
        return Err(anyhow!("パスが存在しません: {}", path.display()));
    }
    if !path.is_file() {
        return Err(anyhow!("パスがファイルではありません: {}", path.display()));
    }
    std::fs::remove_file(path)
        .map_err(|e| anyhow!("ファイルの削除に失敗しました: {}", e))
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
    if !path.exists() {
        return Err(anyhow!("パスが存在しません: {}", path.display()));
    }
    if !path.is_dir() {
        return Err(anyhow!("パスがディレクトリではありません: {}", path.display()));
    }
    std::fs::remove_dir_all(path)
        .map_err(|e| anyhow!("ディレクトリの削除に失敗しました: {}", e))
} 