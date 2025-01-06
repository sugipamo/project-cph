use crate::error::{CphError, DockerError};

pub fn docker_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed { message: msg })
}

pub fn container_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed { message: msg })
}

pub fn compilation_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed { message: msg })
}

pub fn command_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed { message: msg })
}

pub fn state_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed { message: msg })
} 