use std::path::Path;
use std::fs::metadata;
use anyhow::Result;
use crate::error::fs::*;

/// パスが存在するかどうかを確認します
pub fn exists<P: AsRef<Path>>(path: P) -> bool {
    path.as_ref().exists()
}

/// パスがファイルかどうかを確認します
pub fn is_file<P: AsRef<Path>>(path: P) -> bool {
    path.as_ref().is_file()
}

/// パスがディレクトリかどうかを確認します
pub fn is_directory<P: AsRef<Path>>(path: P) -> bool {
    path.as_ref().is_dir()
}

/// パスの権限を確認します
pub fn check_permissions<P: AsRef<Path>>(path: P, write_required: bool) -> Result<()> {
    let path = path.as_ref();
    let metadata = metadata(path)?;
    
    if !metadata.permissions().readonly() && write_required {
        return Err(permission_error(path));
    }
    Ok(())
} 