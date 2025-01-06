use super::*;
use crate::{fs_error, docker_error, contest_error, config_error};

// ファイルシステム関連のヘルパー
pub fn fs_not_found(op: impl Into<String>, path: impl Into<String>) -> CphError {
    fs_error!(op.into(), path.into(), FileSystemErrorKind::NotFound)
}

pub fn fs_permission(op: impl Into<String>, path: impl Into<String>) -> CphError {
    fs_error!(op.into(), path.into(), FileSystemErrorKind::Permission)
}

pub fn fs_io(op: impl Into<String>, path: impl Into<String>, error: std::io::Error) -> CphError {
    fs_error!(op.into(), path.into(), FileSystemErrorKind::Io)
        .with_source(error)
}

// Docker関連のヘルパー
pub fn docker_build(op: impl Into<String>, context: impl Into<String>, error: std::io::Error) -> CphError {
    docker_error!(op.into(), context.into(), DockerErrorKind::BuildFailed)
        .with_source(error)
}

pub fn docker_execution(op: impl Into<String>, context: impl Into<String>, error: std::io::Error) -> CphError {
    docker_error!(op.into(), context.into(), DockerErrorKind::ExecutionFailed)
        .with_source(error)
}

pub fn docker_connection(op: impl Into<String>, context: impl Into<String>) -> CphError {
    docker_error!(op.into(), context.into(), DockerErrorKind::ConnectionFailed)
}

// コンテスト関連のヘルパー
pub fn contest_site(op: impl Into<String>, context: impl Into<String>) -> CphError {
    contest_error!(op.into(), context.into(), ContestErrorKind::Site)
}

pub fn contest_language(op: impl Into<String>, context: impl Into<String>) -> CphError {
    contest_error!(op.into(), context.into(), ContestErrorKind::Language)
}

// 設定関連のヘルパー
pub fn config_not_found(op: impl Into<String>, path: impl Into<String>) -> CphError {
    config_error!(op.into(), path.into(), ConfigErrorKind::NotFound)
}

pub fn config_parse(op: impl Into<String>, path: impl Into<String>) -> CphError {
    config_error!(op.into(), path.into(), ConfigErrorKind::Parse)
}

pub fn config_invalid(op: impl Into<String>, path: impl Into<String>) -> CphError {
    config_error!(op.into(), path.into(), ConfigErrorKind::InvalidValue)
} 