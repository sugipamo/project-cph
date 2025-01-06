use thiserror::Error;
use tokio::time::error::Elapsed;
use crate::docker::state::StateError;

#[derive(Debug, Error)]
pub enum DockerError {
    #[error("コマンドの実行に失敗しました: {0}")]
    Command(String),

    #[error("コンテナの状態エラー: {0}")]
    State(#[from] StateError),

    #[error("タイムアウトエラー")]
    Timeout(#[from] Elapsed),

    #[error("ファイルシステムエラー: {0}")]
    Filesystem(String),

    #[error("システムエラー: {0}")]
    System(String),
}

impl From<nix::errno::Errno> for DockerError {
    fn from(err: nix::errno::Errno) -> Self {
        DockerError::System(err.to_string())
    }
}

impl From<std::io::Error> for DockerError {
    fn from(err: std::io::Error) -> Self {
        DockerError::Filesystem(err.to_string())
    }
}

pub type DockerResult<T> = Result<T, DockerError>; 