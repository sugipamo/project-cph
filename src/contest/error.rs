use thiserror::Error;
use std::io;

#[derive(Error, Debug)]
pub enum ContestError {
    #[error("I/Oエラー: {0}")]
    Io(#[from] io::Error),

    #[error("設定エラー: {0}")]
    Config(String),

    #[error("コンテストエラー: {0}")]
    Contest(String),
}

pub type ContestResult<T> = Result<T, ContestError>;
