use std::fmt;

#[derive(Debug)]
pub enum ContainerError {
    Creation(String),
    Execution(String),
    Communication(String),
    BufferFull(String),
    Internal(String),
}

impl fmt::Display for ContainerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
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