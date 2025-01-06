use thiserror::Error;

#[derive(Error, Debug)]
pub enum DockerError {
    #[error("Dockerコマンドエラー: {0}")]
    Command(String),
    
    #[error("コンテナエラー: {0}")]
    Container(String),
    
    #[error("I/Oエラー: {0}")]
    IO(String),
    
    #[error("コンパイルエラー: {0}")]
    Compilation(String),
}

pub type DockerResult<T> = Result<T, DockerError>; 