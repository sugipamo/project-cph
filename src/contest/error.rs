use thiserror::Error;
use std::io;
use crate::docker::error::DockerError;

#[derive(Error, Debug)]
pub enum ContestError {
    #[error("IO error: {0}")]
    IO(#[from] io::Error),
    
    #[error("Docker error: {0}")]
    Docker(String),
    
    #[error("Invalid configuration: {0}")]
    Config(String),
}

impl From<DockerError> for ContestError {
    fn from(err: DockerError) -> Self {
        ContestError::Docker(err.to_string())
    }
}

pub type ContestResult<T> = Result<T, ContestError>;
