use std::path::StripPrefixError;
use glob::PatternError;

pub type Result<T> = std::result::Result<T, Error>;

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Docker error: {0}")]
    Docker(#[from] DockerError),

    #[error("Invalid input: {0}")]
    InvalidInput(String),

    #[error("YAML error: {0}")]
    Yaml(#[from] serde_yaml::Error),

    #[error("Pattern error: {0}")]
    Pattern(#[from] PatternError),

    #[error("Path error: {0}")]
    Path(#[from] StripPrefixError),
}

#[derive(Debug, thiserror::Error)]
pub enum DockerError {
    #[error("Docker operation failed: {kind} - {source}")]
    Failed {
        kind: &'static str,
        source: std::io::Error,
    },

    #[error("Operation timed out after {0} seconds")]
    Timeout(u64),
}

impl DockerError {
    pub fn failed(kind: &'static str, source: std::io::Error) -> Self {
        Self::Failed { kind, source }
    }
} 