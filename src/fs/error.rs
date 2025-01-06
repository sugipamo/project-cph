use std::error::Error;
use crate::error::CphError;

pub fn fs_err(msg: String) -> Box<dyn Error> {
    Box::new(CphError::Fs(msg))
}

pub fn fs_err_with_source<E: std::error::Error>(msg: &str, source: E) -> Box<dyn Error> {
    Box::new(CphError::Fs(format!("{}: {}", msg, source)))
} 