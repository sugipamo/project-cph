use crate::error::{CphError, helpers, ErrorExt};
use crate::error::docker::DockerErrorKind;

pub fn docker_err(msg: String) -> CphError {
    helpers::docker_error(DockerErrorKind::ExecutionFailed, "Docker操作", msg)
}

pub fn container_err(msg: String) -> CphError {
    helpers::docker_error(DockerErrorKind::ExecutionFailed, "コンテナ操作", msg)
}

pub fn compilation_err(msg: String) -> CphError {
    helpers::docker_error(DockerErrorKind::BuildFailed, "コンパイル", msg)
}

pub fn command_err(msg: String) -> CphError {
    helpers::docker_error(DockerErrorKind::ExecutionFailed, "コマンド実行", msg)
}

pub fn state_err(msg: String) -> CphError {
    helpers::docker_error(DockerErrorKind::StateFailed, "状態管理", msg)
}

pub fn build_err(image: String, context: String) -> CphError {
    helpers::docker_error(DockerErrorKind::BuildFailed, "イメージビルド", &image)
        .with_hint(format!("コンテキスト: {}", context))
}

pub fn build_err_with_hint(image: String, context: String, hint: String) -> CphError {
    helpers::docker_error(DockerErrorKind::BuildFailed, "イメージビルド", &image)
        .with_hint(format!("コンテキスト: {}, ヒント: {}", context, hint))
}

pub fn connection_err() -> CphError {
    helpers::docker_error(DockerErrorKind::ConnectionFailed, "Docker接続", "接続に失敗しました")
} 