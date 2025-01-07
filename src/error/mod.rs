pub mod config;
pub mod contest;
pub mod docker;
pub mod fs;
pub mod helpers;
pub mod macros;

pub use anyhow::{Error, Result, Context as _};

#[derive(Debug, Clone, Copy)]
pub enum ErrorSeverity {
    Warning,
    Error,
    Fatal,
}

pub trait ErrorExt {
    fn severity(&self) -> ErrorSeverity;
    fn with_severity(self, severity: ErrorSeverity) -> Error;
    fn with_hint<C>(self, hint: C) -> Error where C: std::fmt::Display + Send + Sync + 'static;
}

impl ErrorExt for Error {
    fn severity(&self) -> ErrorSeverity {
        ErrorSeverity::Error
    }

    fn with_severity(self, _severity: ErrorSeverity) -> Error {
        self.context(format!("重大度: {:?}", _severity))
    }

    fn with_hint<C>(self, hint: C) -> Error
    where
        C: std::fmt::Display + Send + Sync + 'static,
    {
        self.context(format!("ヒント: {}", hint))
    }
} 