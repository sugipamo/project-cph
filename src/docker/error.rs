use thiserror::Error;
use std::time::Duration;

#[derive(Error, Debug)]
pub enum DockerError {
    #[error("Container operation failed: {0}")]
    Container(String),
    
    #[error("IO operation failed: {0}")]
    IO(String),
    
    #[error("Command execution failed: {0}")]
    Command(String),
    
    #[error("Invalid state: {0}")]
    InvalidState(String),
    
    #[error("Initialization failed: {0}")]
    Initialization(String),
    
    #[error("Timeout after {0:?}")]
    Timeout(Duration),
    
    #[error("Resource exhausted: {0}")]
    ResourceExhausted(String),
}

pub type DockerResult<T> = Result<T, DockerError>;

impl From<std::io::Error> for DockerError {
    fn from(err: std::io::Error) -> Self {
        DockerError::IO(err.to_string())
    }
}

impl From<tokio::time::error::Elapsed> for DockerError {
    fn from(_: tokio::time::error::Elapsed) -> Self {
        DockerError::Timeout(Duration::from_secs(30))
    }
}

#[derive(Debug)]
pub struct ErrorContext {
    pub operation: String,
    pub container_id: Option<String>,
    pub command: Option<String>,
} 