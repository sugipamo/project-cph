use crate::error::{CphError, FileSystemError};

pub fn fs_err(msg: String) -> CphError {
    CphError::Fs(FileSystemError::NotFound { path: msg })
}

pub fn fs_err_with_source(msg: &str, source: impl std::error::Error) -> CphError {
    CphError::Fs(FileSystemError::Io(std::io::Error::new(
        std::io::ErrorKind::Other,
        format!("{}: {}", msg, source),
    )))
} 