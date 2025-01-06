use std::error::Error;
use std::fmt;
use std::io;
use nix::errno::Errno;
use crate::docker::state::StateError;

#[derive(Debug)]
pub enum DockerError {
    Container(String),
    Compilation(String),
    Command(String),
    State(StateError),
    IO(io::Error),
    Filesystem(String),
    System(String),
}

impl fmt::Display for DockerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DockerError::Container(msg) => write!(f, "コンテナエラー: {}", msg),
            DockerError::Compilation(msg) => write!(f, "コンパイルエラー: {}", msg),
            DockerError::Command(msg) => write!(f, "コマンドエラー: {}", msg),
            DockerError::State(err) => write!(f, "状態エラー: {}", err),
            DockerError::IO(err) => write!(f, "I/Oエラー: {}", err),
            DockerError::Filesystem(msg) => write!(f, "ファイルシステムエラー: {}", msg),
            DockerError::System(msg) => write!(f, "システムエラー: {}", msg),
        }
    }
}

impl Error for DockerError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            DockerError::State(err) => Some(err),
            DockerError::IO(err) => Some(err),
            _ => None,
        }
    }
}

impl From<io::Error> for DockerError {
    fn from(err: io::Error) -> Self {
        DockerError::IO(err)
    }
}

impl From<StateError> for DockerError {
    fn from(err: StateError) -> Self {
        DockerError::State(err)
    }
}

impl From<Errno> for DockerError {
    fn from(err: Errno) -> Self {
        DockerError::System(err.to_string())
    }
}

pub type DockerResult<T> = Result<T, DockerError>; 