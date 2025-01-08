use std::path::Path;
use anyhow::{Result, anyhow};
use crate::message::fs;

/// パスの存在を検証します。
/// 
/// # Errors
/// - パスが存在しない場合
pub fn exists(path: &Path) -> Result<()> {
    if !path.exists() {
        return Err(anyhow!(fs::error("file_not_found", path.display())));
    }
    Ok(())
}

/// パスがファイルであることを検証します。
/// 
/// # Errors
/// - パスが存在しない場合
/// - パスがファイルでない場合
pub fn is_file(path: &Path) -> Result<()> {
    exists(path)?;
    if !path.is_file() {
        return Err(anyhow!(fs::error("invalid_path", path.display())));
    }
    Ok(())
}

/// パスがディレクトリであることを検証します。
/// 
/// # Errors
/// - パスが存在しない場合
/// - パスがディレクトリでない場合
pub fn is_dir(path: &Path) -> Result<()> {
    exists(path)?;
    if !path.is_dir() {
        return Err(anyhow!(fs::error("invalid_path", path.display())));
    }
    Ok(())
}

/// パスの親ディレクトリが存在することを検証します。
/// 
/// # Errors
/// - 親ディレクトリが存在しない場合
pub fn parent_exists(path: &Path) -> Result<()> {
    if let Some(parent) = path.parent() {
        exists(parent)?;
    }
    Ok(())
} 