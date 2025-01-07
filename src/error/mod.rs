pub mod config;
pub mod contest;
pub mod docker;
pub mod fs;
pub mod helpers;
pub mod macros;

use std::fmt;
use crate::error::{
    config::ConfigErrorKind,
    fs::FileSystemErrorKind,
    docker::DockerErrorKind,
};

#[derive(Debug, Clone, Copy)]
pub enum ErrorSeverity {
    Warning,
    Error,
    Fatal,
}

pub trait ErrorKind: fmt::Debug + fmt::Display {
    fn severity(&self) -> ErrorSeverity;
}

#[derive(Debug)]
pub struct Error {
    kind: Box<dyn ErrorKind>,
    message: String,
    hint: Option<String>,
}

impl Error {
    pub fn new(kind: impl ErrorKind + 'static, message: impl Into<String>) -> Self {
        Self {
            kind: Box::new(kind),
            message: message.into(),
            hint: None,
        }
    }

    pub fn fs(kind: FileSystemErrorKind, message: impl Into<String>) -> Self {
        Self::new(kind, message)
    }

    pub fn config(kind: ConfigErrorKind, message: impl Into<String>) -> Self {
        Self::new(kind, message)
    }

    pub fn docker(kind: DockerErrorKind, message: impl Into<String>) -> Self {
        Self::new(kind, message)
    }

    pub fn other(message: impl Into<String>) -> Self {
        Self::new(OtherErrorKind(message.into()), "その他のエラー")
    }

    pub fn kind(&self) -> &dyn ErrorKind {
        &*self.kind
    }

    pub fn message(&self) -> &str {
        &self.message
    }

    pub fn hint(&self) -> Option<&str> {
        self.hint.as_deref()
    }

    pub fn with_hint(mut self, hint: impl Into<String>) -> Self {
        self.hint = Some(hint.into());
        self
    }
}

impl std::error::Error for Error {}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.message)?;
        if let Some(hint) = &self.hint {
            write!(f, " (ヒント: {})", hint)?;
        }
        Ok(())
    }
}

impl From<std::io::Error> for Error {
    fn from(error: std::io::Error) -> Self {
        Error::fs(
            FileSystemErrorKind::IO,
            format!("IO error: {}", error)
        )
    }
}

impl From<FileSystemErrorKind> for Error {
    fn from(kind: FileSystemErrorKind) -> Self {
        Error::fs(kind.clone(), kind.to_string())
    }
}

impl From<ConfigErrorKind> for Error {
    fn from(kind: ConfigErrorKind) -> Self {
        Error::config(kind.clone(), kind.to_string())
    }
}

impl From<DockerErrorKind> for Error {
    fn from(kind: DockerErrorKind) -> Self {
        Error::docker(kind.clone(), kind.to_string())
    }
}

#[derive(Debug, Clone)]
struct OtherErrorKind(String);

impl fmt::Display for OtherErrorKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl ErrorKind for OtherErrorKind {
    fn severity(&self) -> ErrorSeverity {
        ErrorSeverity::Error
    }
}

pub type Result<T> = std::result::Result<T, Error>; 