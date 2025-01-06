use crate::error::{CphError, helpers, ErrorExt};

pub fn docker_err(msg: String) -> CphError {
    helpers::docker_execution(msg)
}

pub fn container_err(msg: String) -> CphError {
    helpers::docker_execution(msg)
}

pub fn compilation_err(msg: String) -> CphError {
    helpers::docker_execution(msg)
}

pub fn command_err(msg: String) -> CphError {
    helpers::docker_execution(msg)
}

pub fn state_err(msg: String) -> CphError {
    helpers::docker_execution(msg)
}

pub fn build_err(image: String, context: String) -> CphError {
    helpers::docker_build(format!("イメージ: {}, コンテキスト: {}", image, context))
}

pub fn build_err_with_hint(image: String, context: String, hint: String) -> CphError {
    helpers::docker_build(format!("イメージ: {}, コンテキスト: {}", image, context))
        .with_hint(hint)
}

pub fn connection_err() -> CphError {
    helpers::docker_connection()
} 