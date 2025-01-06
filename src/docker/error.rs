use thiserror::Error;
use std::io;

#[derive(Debug, Error)]
pub enum DockerError {
    #[error("ランタイムエラー: {0}")]
    Runtime(String),
    #[error("タイムアウト: {0}")]
    Timeout(String),
    #[error("メモリ制限超過: {0}")]
    Memory(String),
    #[error("設定エラー: {0}")]
    Config(String),
    #[error("ファイルシステムエラー: {0}")]
    Filesystem(String),
    #[error("I/Oエラー: {0}")]
    Io(#[from] io::Error),
}

pub type DockerResult<T> = Result<T, DockerError>;

impl From<nix::Error> for DockerError {
    fn from(err: nix::Error) -> Self {
        DockerError::Filesystem(err.to_string())
    }
} 