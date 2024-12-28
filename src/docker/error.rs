use thiserror::Error;

#[derive(Error, Debug)]
pub enum DockerError {
    #[error("Docker connection error: {0}")]
    ConnectionError(#[from] bollard::errors::Error),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Yaml parsing error: {0}")]
    YamlError(#[from] serde_yaml::Error),

    #[error("Compilation error: {0}")]
    CompilationError(String),

    #[error("Runtime error: {0}")]
    RuntimeError(String),

    #[error("Timeout error")]
    TimeoutError,

    #[error("Memory limit exceeded")]
    MemoryLimitExceeded,

    #[error("Unsupported language: {0}")]
    UnsupportedLanguage(String),

    #[error("Container not initialized")]
    ContainerNotInitialized,

    #[error("Invalid state transition: {from:?} -> {to:?}")]
    InvalidStateTransition {
        from: String,
        to: String,
    },
}

pub type Result<T> = std::result::Result<T, DockerError>; 