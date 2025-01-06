use std::io;
use std::path::StripPrefixError;
use thiserror::Error;

pub const NO_ACTIVE_CONTEST: &str = "アクティブなコンテストがありません。'work'コマンドで設定してください。";

#[derive(Debug, Error)]
pub enum ConfigError {
    #[error("設定ファイルが見つかりません: {path}\nヒント: 'config.yaml'ファイルが正しい場所にあることを確認してください。")]
    NotFound { path: String },
    
    #[error("設定ファイルの解析に失敗しました: {0}\nヒント: YAMLの構文が正しいことを確認してください。")]
    Parse(#[from] serde_yaml::Error),
    
    #[error("無効な設定値: {field} - {message}\nヒント: {help}")]
    InvalidValue { field: String, message: String, help: String },
}

#[derive(Debug, Error)]
pub enum FileSystemError {
    #[error("ファイルが見つかりません: {path}\nヒント: パスが正しいことを確認してください。")]
    NotFound { path: String },
    
    #[error("アクセス権限がありません: {path}\nヒント: ファイルの権限設定を確認してください。")]
    Permission { path: String },
    
    #[error("IOエラー: {0}\nコンテキスト: {1}")]
    Io(io::Error, String),
    
    #[error("パスエラー: {0}\nヒント: パスが有効であることを確認してください。")]
    Path(#[from] StripPrefixError),
}

#[derive(Debug, Error)]
pub enum LanguageError {
    #[error("サポートされていない言語です: {lang}\nヒント: サポートされている言語は: cpp, python, rust です。")]
    Unsupported { lang: String },
    
    #[error("コンパイラが見つかりません: {compiler}\nヒント: {compiler}がインストールされていることを確認してください。")]
    CompilerNotFound { compiler: String },
    
    #[error("言語設定エラー: {message}\nヒント: {help}")]
    Config { message: String, help: String },
}

#[derive(Debug, Error)]
pub enum DockerError {
    #[error("Dockerデーモンに接続できません\nヒント: Dockerが起動していることを確認してください。")]
    ConnectionFailed,
    
    #[error("イメージのビルドに失敗しました: {image}\nコンテキスト: {context}\nヒント: Dockerfileを確認してください。")]
    BuildFailed { image: String, context: String },
    
    #[error("コンテナの実行に失敗しました: {message}\nコンテキスト: {context}")]
    ExecutionFailed { message: String, context: String },
    
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