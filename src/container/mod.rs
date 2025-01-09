pub mod network;
pub mod execution;
pub mod buffer;

pub use network::{ContainerNetwork, Message, ControlMessage, StatusMessage};
pub use execution::{ParallelExecutor, Container, ContainerConfig};
pub use buffer::OutputBuffer;

use std::path::PathBuf;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ContainerError {
    #[error("コンテナの作成に失敗: {0}")]
    Creation(String),
    #[error("コンテナの実行に失敗: {0}")]
    Execution(String),
    #[error("通信エラー: {0}")]
    Communication(String),
    #[error("バッファが一杯です: {0}")]
    BufferFull(String),
    #[error("内部エラー: {0}")]
    Internal(String),
}

/// コンテナの状態
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ContainerStatus {
    Created,
    Running,
    Completed,
    Failed(String),
}

pub type Result<T> = std::result::Result<T, ContainerError>; 