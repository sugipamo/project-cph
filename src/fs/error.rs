use crate::error::{CphError, FileSystemError};

pub fn fs_err(msg: String) -> CphError {
    CphError::Fs(FileSystemError::NotFound { path: msg })
}

pub fn fs_err_with_source(msg: &str, source: impl std::error::Error) -> CphError {
    CphError::Fs(FileSystemError::Io(
        std::io::Error::new(std::io::ErrorKind::Other, format!("{}: {}", msg, source)),
        "ファイルシステム操作中のエラー".to_string(),
    ))
}

#[allow(dead_code)]
pub fn fs_permission_err(path: String) -> CphError {
    CphError::Fs(FileSystemError::Permission { path })
}

#[allow(dead_code)]
pub fn fs_io_err(error: std::io::Error, context: String) -> CphError {
    CphError::Fs(FileSystemError::Io(error, context))
} 