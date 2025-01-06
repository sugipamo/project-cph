use std::error::Error;
use std::fmt;

#[derive(Debug, Clone, PartialEq)]
pub enum DockerError {
    Initialization(String),
    State(String),
    Command(String),
    IO(String),
    Timeout(String),
    System(String),
}

impl Error for DockerError {}

impl fmt::Display for DockerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DockerError::Initialization(msg) => write!(f, "初期化エラー: {}", msg),
            DockerError::State(msg) => write!(f, "状態エラー: {}", msg),
            DockerError::Command(msg) => write!(f, "コマンドエラー: {}", msg),
            DockerError::IO(msg) => write!(f, "I/Oエラー: {}", msg),
            DockerError::Timeout(msg) => write!(f, "タイムアウトエラー: {}", msg),
            DockerError::System(msg) => write!(f, "システムエラー: {}", msg),
        }
    }
}

pub type DockerResult<T> = Result<T, DockerError>;

impl From<std::io::Error> for DockerError {
    fn from(err: std::io::Error) -> Self {
        DockerError::IO(err.to_string())
    }
}

impl From<tokio::time::error::Elapsed> for DockerError {
    fn from(_: tokio::time::error::Elapsed) -> Self {
        DockerError::Timeout("操作がタイムアウトしました".to_string())
    }
}

#[derive(Debug)]
pub struct ErrorContext {
    pub operation: String,
    pub container_id: Option<String>,
    pub command: Option<String>,
} 