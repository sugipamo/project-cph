use thiserror::Error;

#[derive(Error, Debug)]
pub enum DockerError {
    #[error("設定エラー: {0}")]
    Config(String),

    #[error("コンテナ操作エラー: {0}")]
    Container(String),

    #[error("I/O エラー: {0}")]
    IO(String),

    #[error("コンパイルエラー: {0}")]
    Compilation(String),

    #[error("タイムアウトエラー: {0}")]
    Timeout(String),

    #[error("ランタイムエラー: {0}")]
    Runtime(String),
}

pub type DockerResult<T> = Result<T, DockerError>; 