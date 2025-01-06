use crate::error::{CphError, helpers, ErrorExt};

pub fn docker_err(msg: String) -> CphError {
    helpers::docker_execution("Docker操作", "Docker", Box::new(std::io::Error::new(std::io::ErrorKind::Other, msg)))
}

pub fn container_err(msg: String) -> CphError {
    helpers::docker_execution("コンテナ操作", "Container", Box::new(std::io::Error::new(std::io::ErrorKind::Other, msg)))
}

pub fn compilation_err(msg: String) -> CphError {
    helpers::docker_execution("コンパイル", "Compiler", Box::new(std::io::Error::new(std::io::ErrorKind::Other, msg)))
}

pub fn command_err(msg: String) -> CphError {
    helpers::docker_execution("コマンド実行", "Command", Box::new(std::io::Error::new(std::io::ErrorKind::Other, msg)))
}

pub fn state_err(msg: String) -> CphError {
    helpers::docker_execution("状態管理", "State", Box::new(std::io::Error::new(std::io::ErrorKind::Other, msg)))
}

pub fn build_err(image: String, context: String) -> CphError {
    helpers::docker_build(
        "イメージビルド",
        &image,
        Box::new(std::io::Error::new(std::io::ErrorKind::Other, format!("コンテキスト: {}", context)))
    )
}

pub fn build_err_with_hint(image: String, context: String, hint: String) -> CphError {
    helpers::docker_build(
        "イメージビルド",
        &image,
        Box::new(std::io::Error::new(std::io::ErrorKind::Other, format!("コンテキスト: {}", context)))
    ).with_hint(hint)
}

pub fn connection_err() -> CphError {
    helpers::docker_connection("Docker接続")
} 