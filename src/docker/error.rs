use std::fmt;
use std::error::Error;

#[derive(Debug)]
pub enum DockerError {
    Config(String),
    Runtime(String),
    Timeout(String),
    Memory(String),
    IO(std::io::Error),
}

impl fmt::Display for DockerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DockerError::Config(msg) => write!(f, "Docker設定エラー: {}", msg),
            DockerError::Runtime(msg) => write!(f, "Docker実行時エラー: {}", msg),
            DockerError::Timeout(msg) => write!(f, "Dockerタイムアウトエラー: {}", msg),
            DockerError::Memory(msg) => write!(f, "Dockerメモリ制限エラー: {}", msg),
            DockerError::IO(err) => write!(f, "Docker I/Oエラー: {}", err),
        }
    }
}

impl Error for DockerError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            DockerError::IO(err) => Some(err),
            _ => None,
        }
    }
}

impl From<std::io::Error> for DockerError {
    fn from(err: std::io::Error) -> Self {
        DockerError::IO(err)
    }
}

// 便利なResult型エイリアス
pub type DockerResult<T> = Result<T, DockerError>; 