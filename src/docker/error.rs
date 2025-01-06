use crate::error::{CphError, DockerError};

pub fn docker_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed {
        message: msg,
        context: "Docker操作中のエラー".to_string(),
    })
}

pub fn container_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed {
        message: msg,
        context: "コンテナ操作中のエラー".to_string(),
    })
}

pub fn compilation_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed {
        message: msg,
        context: "コンパイル中のエラー".to_string(),
    })
}

pub fn command_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed {
        message: msg,
        context: "コマンド実行中のエラー".to_string(),
    })
}

pub fn state_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed {
        message: msg,
        context: "コンテナの状態遷移中のエラー".to_string(),
    })
}

pub fn build_err(image: String, context: String) -> CphError {
    CphError::Docker(DockerError::BuildFailed { image, context })
}

pub fn connection_err() -> CphError {
    CphError::Docker(DockerError::ConnectionFailed)
} 