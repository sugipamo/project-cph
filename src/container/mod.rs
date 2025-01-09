pub mod network;
pub mod execution;
pub mod buffer;

pub use network::{ContainerNetwork, Message, ControlMessage, StatusMessage};
pub use execution::{ParallelExecutor, Container, ContainerConfig};
pub use buffer::OutputBuffer;

use std::path::PathBuf;
use anyhow::{Error, Result};

#[derive(Debug)]
pub enum ContainerError {
    Creation(String),
    Execution(String),
    Communication(String),
    BufferFull(String),
    Internal(String),
}

impl std::fmt::Display for ContainerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Creation(msg) => write!(f, "コンテナの作成に失敗: {msg}"),
            Self::Execution(msg) => write!(f, "コンテナの実行に失敗: {msg}"),
            Self::Communication(msg) => write!(f, "通信エラー: {msg}"),
            Self::BufferFull(msg) => write!(f, "バッファが一杯です: {msg}"),
            Self::Internal(msg) => write!(f, "内部エラー: {msg}"),
        }
    }
}

impl std::error::Error for ContainerError {}

/// コンテナの状態
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ContainerStatus {
    Created,
    Running,
    Completed,
    Failed(String),
}

pub type Result<T> = std::result::Result<T, ContainerError>; 