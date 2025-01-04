use std::path::PathBuf;

/// コンテスト操作に関するエラー
#[derive(Debug)]
pub enum ContestError {
    /// ファイル操作エラー
    FileError {
        source: std::io::Error,
        path: PathBuf,
    },
    /// 設定エラー
    ConfigError(String),
    /// バリデーションエラー
    ValidationError(String),
}

impl std::fmt::Display for ContestError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::FileError { source, path } => {
                write!(f, "ファイル操作エラー ({}): {}", path.display(), source)
            }
            Self::ConfigError(msg) => write!(f, "設定エラー: {}", msg),
            Self::ValidationError(msg) => write!(f, "検証エラー: {}", msg),
        }
    }
}

impl std::error::Error for ContestError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::FileError { source, .. } => Some(source),
            _ => None,
        }
    }
}

impl From<std::io::Error> for ContestError {
    fn from(error: std::io::Error) -> Self {
        Self::FileError {
            source: error,
            path: PathBuf::from("."),
        }
    }
}

impl From<serde_yaml::Error> for ContestError {
    fn from(error: serde_yaml::Error) -> Self {
        Self::ConfigError(error.to_string())
    }
}

impl From<String> for ContestError {
    fn from(error: String) -> Self {
        Self::ConfigError(error)
    }
}

pub type Result<T> = std::result::Result<T, ContestError>; 