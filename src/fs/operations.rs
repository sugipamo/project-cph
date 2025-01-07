use std::path::{Path, PathBuf};
use crate::error::Error;
use crate::fs::error::{not_found_err, io_err};

pub fn ensure_directory<P: AsRef<Path>>(path: P) -> Result<PathBuf, Error> {
    let path = path.as_ref();
    if !path.exists() {
        std::fs::create_dir_all(path)
            .map_err(|e| io_err(e, format!("ディレクトリの作成に失敗: {}", path.display())))?;
    }
    Ok(path.to_path_buf())
}

pub fn ensure_file<P: AsRef<Path>>(path: P) -> Result<PathBuf, Error> {
    let path = path.as_ref();
    if !path.exists() {
        if let Some(parent) = path.parent() {
            ensure_directory(parent)?;
        }
        std::fs::write(path, "")
            .map_err(|e| io_err(e, format!("ファイルの作成に失敗: {}", path.display())))?;
    }
    Ok(path.to_path_buf())
}

pub fn read_file<P: AsRef<Path>>(path: P) -> Result<String, Error> {
    let path = path.as_ref();
    if !path.exists() {
        return Err(not_found_err(path.to_string_lossy().to_string()));
    }
    std::fs::read_to_string(path)
        .map_err(|e| io_err(e, format!("ファイルの読み込みに失敗: {}", path.display())))
}

pub fn write_file<P: AsRef<Path>>(path: P, content: &str) -> Result<(), Error> {
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        ensure_directory(parent)?;
    }
    std::fs::write(path, content)
        .map_err(|e| io_err(e, format!("ファイルの書き込みに失敗: {}", path.display())))
} 