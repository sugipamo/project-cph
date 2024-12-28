use std::io;
use std::path::StripPrefixError;
use thiserror::Error;

pub const NO_ACTIVE_CONTEST: &str = "No active contest. Use 'workspace' command to set one.";

#[derive(Debug, Error)]
pub enum Error {
    #[error("IO error: {0}")]
    Io(#[from] io::Error),

    #[error("Docker error: {0}")]
    Docker(String),

    #[error("Config error: {0}")]
    Config(String),

    #[error("Invalid input: {0}")]
    InvalidInput(String),

    #[error("YAML error: {0}")]
    Yaml(#[from] serde_yaml::Error),

    #[error("Path error: {0}")]
    Path(#[from] StripPrefixError),
}

impl Error {
    pub fn invalid_input<T, S: Into<String>>(message: S) -> Result<T> {
        Err(Error::InvalidInput(message.into()))
    }

    pub fn command_failed(command: &str, error: String) -> Self {
        Error::InvalidInput(format!("Command '{}' failed: {}", command, error))
    }

    pub fn unsupported_feature<T>(feature: &str) -> Result<T> {
        Error::invalid_input(format!("{} is not supported yet", feature))
    }
}

pub type Result<T> = std::result::Result<T, Error>; 