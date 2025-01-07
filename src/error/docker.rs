use std::fmt;
use crate::error::{Error, ErrorSeverity};

pub fn docker_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::new(
        DockerErrorKind::Other(error.into()),
        message
    ).with_hint("Dockerの操作に失敗しました")
}

#[derive(Debug, Clone)]
pub enum DockerErrorKind {
    ContainerNotFound,
    ImageNotFound,
    NetworkError,
    ExecutionError,
    CompilationError,
    ValidationError,
    Other(String),
}

impl ErrorKind for DockerErrorKind {
    fn severity(&self) -> ErrorSeverity {
        match self {
            Self::NetworkError => ErrorSeverity::Fatal,
            Self::ExecutionError | Self::CompilationError => ErrorSeverity::Error,
            _ => ErrorSeverity::Warning,
        }
    }
}

impl fmt::Display for DockerErrorKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ContainerNotFound => write!(f, "コンテナが見つかりません"),
            Self::ImageNotFound => write!(f, "イメージが見つかりません"),
            Self::NetworkError => write!(f, "ネットワークエラー"),
            Self::ExecutionError => write!(f, "実行エラー"),
            Self::CompilationError => write!(f, "コンパイルエラー"),
            Self::ValidationError => write!(f, "検証エラー"),
            Self::Other(s) => write!(f, "{}", s),
        }
    }
} 