use std::path::Path;
use anyhow::{Result, anyhow};
use crate::message::fs;

/// パスの存在を検証します。
pub(super) fn validate_exists(path: &Path) -> Result<()> {
    if !path.exists() {
        return Err(anyhow!(fs::error("file_not_found", path.display())));
    }
    Ok(())
}

/// パスがファイルであることを検証します。
pub(super) fn validate_is_file(path: &Path) -> Result<()> {
    validate_exists(path)?;
    if !path.is_file() {
        return Err(anyhow!(fs::error("invalid_path", path.display())));
    }
    Ok(())
}

/// パスがディレクトリであることを検証します。
pub(super) fn validate_is_dir(path: &Path) -> Result<()> {
    validate_exists(path)?;
    if !path.is_dir() {
        return Err(anyhow!(fs::error("invalid_path", path.display())));
    }
    Ok(())
}

/// パスの親ディレクトリが存在することを検証します。
pub(super) fn validate_parent_exists(path: &Path) -> Result<()> {
    if let Some(parent) = path.parent() {
        validate_exists(parent)?;
    }
    Ok(())
} 