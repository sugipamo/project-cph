use crate::fs::error::{invalid_path_error, ErrorExt};
use anyhow::Result;
use std::path::Path;

pub fn create_dir(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if path.exists() {
        if path.is_dir() {
            return Ok(());
        }
        return Err(invalid_path_error(path));
    }
    std::fs::create_dir_all(path)
        .with_context_io(format!("ディレクトリの作成に失敗: {}", path.display()))?;
    Ok(())
}

pub fn create_file(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if path.exists() {
        if path.is_file() {
            return Ok(());
        }
        return Err(invalid_path_error(path));
    }
    if let Some(parent) = path.parent() {
        create_dir(parent)?;
    }
    std::fs::write(path, "")
        .with_context_io(format!("ファイルの作成に失敗: {}", path.display()))?;
    Ok(())
}

pub fn write_file(path: impl AsRef<Path>, content: impl AsRef<[u8]>) -> Result<()> {
    let path = path.as_ref();
    if path.exists() && !path.is_file() {
        return Err(invalid_path_error(path));
    }
    if let Some(parent) = path.parent() {
        create_dir(parent)?;
    }
    std::fs::write(path, content)
        .with_context_io(format!("ファイルの書き込みに失敗: {}", path.display()))
} 