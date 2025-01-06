use crate::error::CphError;

pub fn fs_err(msg: String) -> CphError {
    CphError::Fs(msg)
}

pub fn fs_err_with_source<E: std::error::Error>(msg: &str, source: E) -> CphError {
    CphError::Fs(format!("{}: {}", msg, source))
} 