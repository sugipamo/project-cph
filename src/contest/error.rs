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

pub type Result<T> = std::result::Result<T, ContestError>; 