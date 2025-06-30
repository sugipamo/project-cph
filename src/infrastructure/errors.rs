use thiserror::Error;
use std::io;

#[derive(Error, Debug)]
pub enum InfrastructureError {
    #[error("File system error: {0}")]
    FileSystem(#[from] io::Error),
    
    #[error("Docker error: {0}")]
    Docker(String),
    
    #[error("Shell execution error: {message}")]
    ShellExecution { message: String, exit_code: Option<i32> },
    
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    
    #[error("Network error: {0}")]
    Network(#[from] reqwest::Error),
    
    #[error("Serialization error: {0}")]
    Serialization(String),
    
    #[error("Configuration loading error: {0}")]
    ConfigurationLoading(String),
}