use crate::error::{CphError, helpers, ErrorExt};

pub fn docker_err(msg: String) -> CphError {
    helpers::docker_build(
        "Docker操作",
        "Docker",
        std::io::Error::new(std::io::ErrorKind::Other, msg)
    )
}

pub fn container_err(msg: String) -> CphError {
    helpers::docker_build(
        "コンテナ操作",
        "Container",
        std::io::Error::new(std::io::ErrorKind::Other, msg)
    )
}

pub fn compilation_err(msg: String) -> CphError {
    helpers::docker_build(
        "コンパイル",
        "Compiler",
        std::io::Error::new(std::io::ErrorKind::Other, msg)
    )
}

pub fn command_err(msg: String) -> CphError {
    helpers::docker_build(
        "コマンド実行",
        "Command",
        std::io::Error::new(std::io::ErrorKind::Other, msg)
    )
}

pub fn state_err(msg: String) -> CphError {
    helpers::docker_build(
        "状態管理",
        "State",
        std::io::Error::new(std::io::ErrorKind::Other, msg)
    )
}

pub fn build_err(image: String, context: String) -> CphError {
    helpers::docker_build(
        "イメージビルド",
        &image,
        std::io::Error::new(std::io::ErrorKind::Other, format!("コンテキスト: {}", context))
    )
}

pub fn build_err_with_hint(image: String, context: String, hint: String) -> CphError {
    helpers::docker_build(
        "イメージビルド",
        &image,
        std::io::Error::new(std::io::ErrorKind::Other, format!("コンテキスト: {}", context))
    ).with_hint(hint)
}

pub fn connection_err() -> CphError {
    helpers::docker_connection("Docker接続", "デーモン接続")
} 