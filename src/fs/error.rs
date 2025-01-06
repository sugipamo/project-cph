use crate::error::{CphError, FileSystemError};

pub fn not_found_err(path: String) -> CphError {
    CphError::Fs(FileSystemError::NotFound {
        path,
        hint: None,
    })
}

pub fn io_err(error: std::io::Error, context: String) -> CphError {
    CphError::Fs(FileSystemError::Io {
        source: error,
        context,
    })
}

pub fn permission_err(path: String) -> CphError {
    CphError::Fs(FileSystemError::Permission {
        path,
        hint: None,
    })
}

pub fn transaction_err(error: std::io::Error, context: String) -> CphError {
    CphError::Fs(FileSystemError::Io {
        source: error,
        context,
    })
} 