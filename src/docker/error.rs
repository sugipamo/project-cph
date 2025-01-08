use anyhow::Error;

pub type DockerResult<T> = Result<T, Error>;

pub fn docker_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(error.into()).context(message.into())
}

pub fn execution_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg("実行エラー").context(format!("{}: {}", message.into(), error.into()))
}

pub fn compilation_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg("コンパイルエラー").context(format!("{}: {}", message.into(), error.into()))
}

pub fn container_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg("コンテナエラー").context(format!("{}: {}", message.into(), error.into()))
}

pub fn state_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg("状態エラー").context(format!("{}: {}", message.into(), error.into()))
} 