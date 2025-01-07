use std::fmt;
use crate::error::{
    Error,
    ErrorKind,
    ErrorSeverity,
    config::ConfigErrorKind,
    docker::DockerErrorKind,
    fs::FileSystemErrorKind,
};

pub fn fs_error(kind: FileSystemErrorKind, message: impl Into<String>) -> Error {
    Error::new(kind, message)
}

pub fn docker_error(kind: DockerErrorKind, message: impl Into<String>) -> Error {
    Error::new(kind, message)
}

pub fn config_error(kind: ConfigErrorKind, message: impl Into<String>) -> Error {
    Error::new(kind, message)
}

pub fn other_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::new(
        OtherErrorKind(error.into()),
        message
    ).with_hint("予期しないエラーが発生しました")
}

#[derive(Debug, Clone)]
pub struct OtherErrorKind(String);

impl ErrorKind for OtherErrorKind {
    fn severity(&self) -> ErrorSeverity {
        ErrorSeverity::Error
    }
}

impl fmt::Display for OtherErrorKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}