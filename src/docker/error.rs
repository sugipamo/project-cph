use crate::error::{CphError, DockerError};

pub fn docker_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed {
        message: msg,
        context: "Docker操作".to_string(),
    })
}

pub fn container_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed {
        message: msg,
        context: "コンテナ操作".to_string(),
    })
}

pub fn compilation_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed {
        message: msg,
        context: "コンパイル処理".to_string(),
    })
}

pub fn command_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed {
        message: msg,
        context: "コマンド実行".to_string(),
    })
}

pub fn state_err(msg: String) -> CphError {
    CphError::Docker(DockerError::ExecutionFailed {
        message: msg,
        context: "コンテナの状態管理".to_string(),
    })
}

pub fn build_err(image: String, context: String) -> CphError {
    CphError::Docker(DockerError::BuildFailed {
        image,
        context,
        hint: Some("Dockerfileの構文とビルド設定を確認してください。".to_string()),
    })
}

pub fn build_err_with_hint(image: String, context: String, hint: String) -> CphError {
    CphError::Docker(DockerError::BuildFailed {
        image,
        context,
        hint: Some(hint),
    })
}

pub fn connection_err() -> CphError {
    CphError::Docker(DockerError::ConnectionFailed)
}

/// エラーにコンテキストを追加するためのトレイト
pub trait ErrorExt<T> {
    fn with_context(self, context: impl Into<String>) -> Result<T, CphError>;
    fn with_hint(self, hint: impl Into<String>) -> Result<T, CphError>;
}

impl<T, E: Into<CphError>> ErrorExt<T> for Result<T, E> {
    fn with_context(self, context: impl Into<String>) -> Result<T, CphError> {
        self.map_err(|e| {
            let error = e.into();
            match error {
                CphError::Docker(DockerError::ExecutionFailed { message, .. }) => {
                    CphError::Docker(DockerError::ExecutionFailed {
                        message,
                        context: context.into(),
                    })
                }
                _ => error,
            }
        })
    }

    fn with_hint(self, hint: impl Into<String>) -> Result<T, CphError> {
        self.map_err(|e| {
            let error = e.into();
            match error {
                CphError::Docker(DockerError::BuildFailed { image, context, .. }) => {
                    CphError::Docker(DockerError::BuildFailed {
                        image,
                        context,
                        hint: Some(hint.into()),
                    })
                }
                _ => error,
            }
        })
    }
} 