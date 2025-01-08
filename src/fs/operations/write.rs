use std::path::Path;
use anyhow::{Result, anyhow};
use crate::message::fs;
use super::validate::parent_exists;

/// ディレクトリが存在することを確認し、存在しない場合は作成します。
/// 
/// # Arguments
/// * `path` - 確認または作成するディレクトリのパス
/// 
/// # Errors
/// - ディレクトリの作成に失敗した場合
pub fn ensure_directory(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        std::fs::create_dir_all(path)
            .map_err(|e| anyhow!(fs::error("write_error", e)))?;
    }
    Ok(())
}

/// ファイルが存在することを確認し、存在しない場合は作成します。
/// 
/// # Arguments
/// * `path` - 確認または作成するファイルのパス
/// 
/// # Errors
/// - ファイルの作成に失敗した場合
/// - パスの親ディレクトリの作成に失敗した場合
pub fn ensure_file(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        parent_exists(path)?;
        std::fs::File::create(path)
            .map_err(|e| anyhow!(fs::error("write_error", e)))?;
    }
    Ok(())
}

/// ファイルに内容を書き込みます。
/// 
/// # Arguments
/// * `path` - 書き込み先のファイルパス
/// * `content` - 書き込む内容
/// 
/// # Errors
/// - ファイルの作成に失敗した場合
/// - ファイルの書き込みに失敗した場合
pub fn save_to_file(path: impl AsRef<Path>, content: impl AsRef<[u8]>) -> Result<()> {
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        ensure_directory(parent)?;
    }
    std::fs::write(path, content)
        .map_err(|e| anyhow!(fs::error("write_error", e)))
} 