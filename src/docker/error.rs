use crate::error::Error;
use crate::error::docker::DockerErrorKind;

pub type DockerResult<T> = Result<T, Error>;

pub fn docker_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::docker(
        DockerErrorKind::Other(error.into()),
        message
    )
}

pub fn execution_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::docker(
        DockerErrorKind::ExecutionError,
        message
    )
}

pub fn compilation_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::docker(
        DockerErrorKind::CompilationError,
        message
    )
}

pub fn container_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::docker(
        DockerErrorKind::ContainerNotFound,
        message
    )
}

pub fn state_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::docker(
        DockerErrorKind::ValidationError,
        message
    )
} 