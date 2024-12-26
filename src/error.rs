use std::io;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum Error {
    #[error("Invalid input: {0}")]
    Input(#[from] InputError),
    
    #[error("Test error: {0}")]
    Test(String),
    
    #[error("Docker error: {0}")]
    Docker(#[from] DockerError),
    
    #[error("IO error: {0}")]
    Io(#[from] io::Error),

    #[error("Runtime error: {0}")]
    Runtime(String),
}

#[derive(Debug, Error)]
pub enum InputError {
    #[error("Invalid {kind}: {value}")]
    InvalidValue { kind: &'static str, value: String },
    
    #[error("Missing {0}")]
    Missing(&'static str),
    
    #[error("Invalid format: {0}")]
    Format(String),
}

#[derive(Debug, Error)]
pub enum DockerError {
    #[error("Docker command failed: {0}")]
    CommandFailed(String),
    
    #[error("Docker execution error: {0}")]
    Execution(String),
    
    #[error("Docker timeout after {0} seconds")]
    Timeout(u64),
}

impl DockerError {
    pub fn failed(operation: &str, error: impl std::fmt::Display) -> Self {
        DockerError::Execution(format!("Failed to {}: {}", operation, error))
    }
}

pub type Result<T> = std::result::Result<T, Error>; 