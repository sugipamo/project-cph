use std::io;
use std::path::StripPrefixError;
use thiserror::Error;

pub const NO_ACTIVE_CONTEST: &str = "アクティブなコンテストがありません。'work'コマンドで設定してください。";

/// エラーコンテキストを表す構造体
#[derive(Debug, Clone)]
pub struct ErrorContext {
    pub operation: String,
    pub location: String,
    pub hint: Option<String>,
}

impl ErrorContext {
    pub fn new(operation: impl Into<String>, location: impl Into<String>) -> Self {
        Self {
            operation: operation.into(),
            location: location.into(),
            hint: None,
        }
    }

    pub fn with_hint(mut self, hint: impl Into<String>) -> Self {
        self.hint = Some(hint.into());
        self
    }
}

#[derive(Debug, Error)]
pub enum ConfigError {
    #[error("設定ファイルが見つかりません\n場所: {path}\nヒント: {}", .hint.as_deref().unwrap_or("'config.yaml'ファイルが正しい場所にあることを確認してください。"))]
    NotFound { 
        path: String,
        hint: Option<String>,
    },
    
    #[error("設定ファイルの解析に失敗しました\n原因: {source}\nヒント: YAMLの構文が正しいことを確認してください。")]
    Parse {
        #[from]
        source: serde_yaml::Error,
    },
    
    #[error("無効な設定値\nフィールド: {field}\n内容: {message}\nヒント: {help}")]
    InvalidValue { 
        field: String,
        message: String,
        help: String,
    },
}

#[derive(Debug, Error)]
pub enum FileSystemError {
    #[error("ファイルが見つかりません\n場所: {path}\nヒント: {}", .hint.as_deref().unwrap_or("パスが正しいことを確認してください。"))]
    NotFound { 
        path: String,
        hint: Option<String>,
    },
    
    #[error("アクセス権限がありません\n場所: {path}\nヒント: {}", .hint.as_deref().unwrap_or("ファイルの権限設定を確認してください。"))]
    Permission { 
        path: String,
        hint: Option<String>,
    },
    
    #[error("IOエラー\n操作: {context}\n原因: {source}")]
    Io {
        source: io::Error,
        context: String,
    },
    
    #[error("パスエラー\n原因: {source}\nヒント: パスが有効であることを確認してください。")]
    Path {
        #[from]
        source: StripPrefixError,
    },
}

#[derive(Debug, Error)]
pub enum LanguageError {
    #[error("サポートされていない言語です\n言語: {lang}\nヒント: サポートされている言語は: cpp, python, rust です。")]
    Unsupported { 
        lang: String,
    },
    
    #[error("コンパイラが見つかりません\nコンパイラ: {compiler}\nヒント: {compiler}がインストールされていることを確認してください。")]
    CompilerNotFound { 
        compiler: String,
    },
    
    #[error("言語設定エラー\n内容: {message}\nヒント: {help}")]
    Config { 
        message: String,
        help: String,
    },
}

#[derive(Debug, Error)]
pub enum DockerError {
    #[error("Dockerデーモンに接続できません\nヒント: Dockerが起動していることを確認してください。")]
    ConnectionFailed,
    
    #[error("イメージのビルドに失敗しました\nイメージ: {image}\nコンテキスト: {context}\nヒント: {}", .hint.as_deref().unwrap_or("Dockerfileを確認してください。"))]
    BuildFailed { 
        image: String,
        context: String,
        hint: Option<String>,
    },
    
    #[error("コンテナの実行に失敗しました\n操作: {context}\n内容: {message}")]
    ExecutionFailed { 
        message: String,
        context: String,
    },
    
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
    
    #[error("サイトエラー\n内容: {message}\nヒント: {}", .hint.as_deref().unwrap_or("サイトの設定を確認してください。"))]
    Site { 
        message: String,
        hint: Option<String>,
    },
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
    
    #[error("{message}\nヒント: {}", .hint.as_deref().unwrap_or("詳細については、ドキュメントを参照してください。"))]
    Other { 
        message: String,
        hint: Option<String>,
    },
}

pub type Result<T> = std::result::Result<T, CphError>; 