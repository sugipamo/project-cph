use anyhow::Error;

pub type DockerResult<T> = Result<T, Error>;

pub fn docker_err(error: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("{}: {}", message.into(), error.into()))
}

pub fn execution_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("実行エラー: {}", message.into()))
}

pub fn compilation_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("コンパイルエラー: {}", message.into()))
}

pub fn container_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("コンテナエラー: {}", message.into()))
}

pub fn state_err(_: impl Into<String>, message: impl Into<String>) -> Error {
    Error::msg(format!("状態エラー: {}", message.into()))
} 