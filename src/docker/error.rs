use thiserror::Error;
use crate::docker::state::StateError;

#[derive(Error, Debug)]
pub enum DockerError {
    #[error("Container error: {0}")]
    Container(String),
    #[error("IO error: {0}")]
    IO(String),
    #[error("Compilation error: {0}")]
    Compilation(String),
    #[error("Command error: {0}")]
    Command(String),
    #[error("State error: {0}")]
    State(#[from] StateError),
}

pub type DockerResult<T> = Result<T, DockerError>;

impl From<std::io::Error> for DockerError {
    fn from(err: std::io::Error) -> Self {
        DockerError::IO(err.to_string())
    }
}

impl From<tokio::time::error::Elapsed> for DockerError {
    fn from(err: tokio::time::error::Elapsed) -> Self {
        DockerError::Command(format!("操作がタイムアウトしました: {}", err))
    }
}

#[derive(Debug)]
pub struct ErrorContext {
    pub operation: String,
    pub container_id: Option<String>,
    pub command: Option<String>,
} 