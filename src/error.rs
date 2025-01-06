use std::io;
use std::path::StripPrefixError;
use thiserror::Error;

pub const NO_ACTIVE_CONTEST: &str = "アクティブなコンテストがありません。'work'コマンドで設定してください。";

#[derive(Debug, Error)]
pub enum ConfigError {
    #[error("設定ファイルが見つかりません: {path}")]
    NotFound { path: String },
    
    #[error("設定ファイルの解析に失敗しました: {0}")]
    Parse(#[from] serde_yaml::Error),
    
    #[error("無効な設定値: {field} - {message}")]
    InvalidValue { field: String, message: String },
}

#[derive(Debug, Error)]
pub enum FileSystemError {
    #[error("ファイルが見つかりません: {path}")]
    NotFound { path: String },
    
    #[error("アクセス権限がありません: {path}")]
    Permission { path: String },
    
    #[error("IOエラー: {0}")]
    Io(#[from] io::Error),
    
    #[error("パスエラー: {0}")]
    Path(#[from] StripPrefixError),
}

#[derive(Debug, Error)]
pub enum LanguageError {
    #[error("サポートされていない言語です: {lang}")]
    Unsupported { lang: String },
    
    #[error("コンパイラが見つかりません: {compiler}")]
    CompilerNotFound { compiler: String },
    
    #[error("言語設定エラー: {message}")]
    Config { message: String },
}

#[derive(Debug, Error)]
pub enum DockerError {
    #[error("Dockerデーモンに接続できません")]
    ConnectionFailed,
    
    #[error("イメージのビルドに失敗しました: {image}")]
    BuildFailed { image: String },
    
    #[error("コンテナの実行に失敗しました: {message}")]
    ExecutionFailed { message: String },
    
    #[error("ファイルシステムエラー: {0}")]
    Fs(#[from] FileSystemError),
}

#[derive(Debug, Error)]
pub enum ContestError {
    #[error("設定エラー: {0}")]
    Config(#[from] ConfigError),
    
    #[error("ファイルシステムエラー: {0}")]
    FileSystem(#[from] FileSystemError),
    
    #[error("言語エラー: {0}")]
    Language(#[from] LanguageError),
    
    #[error("サイトエラー: {message}")]
    Site { message: String },
}

#[derive(Debug, Error)]
pub enum CphError {
    #[error("{0}")]
    Contest(#[from] ContestError),
    
    #[error("{0}")]
    Docker(#[from] DockerError),
    
    #[error("{0}")]
    Config(#[from] ConfigError),
    
    #[error("{0}")]
    Fs(#[from] FileSystemError),
    
    #[error("{message}")]
    Other { message: String },
}

pub type Result<T> = std::result::Result<T, CphError>; 