use thiserror::Error;

#[derive(Debug, Error)]
pub enum DockerError {
    #[error("Docker connection error: {0}")]
    ConnectionError(#[from] bollard::errors::Error),

    #[error("Invalid state transition from {from} to {to}")]
    InvalidStateTransition {
        from: String,
        to: String,
    },

    #[error("Container inspection error: {0}")]
    InspectError(String),

    #[error("Container stop error: {0}")]
    StopError(String),

    #[error("Operation timed out")]
    Timeout,

    #[error("Unsupported language: {0}")]
    UnsupportedLanguage(String),

    #[error("Runtime error: {0}")]
    RuntimeError(String),

    #[error("Compilation error: {0}")]
    CompilationError(String),

    #[error("Container not initialized")]
    ContainerNotInitialized,

    #[error("Image pull error: {0}")]
    ImagePullError(String),
}

pub type Result<T> = std::result::Result<T, DockerError>; 