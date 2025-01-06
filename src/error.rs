use std::io;
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

/// 共通のエラー型
#[derive(Debug, Error)]
pub enum CphError {
    #[error("ファイルシステムエラー\n{kind}\n場所: {path}\nヒント: {}", .hint.as_deref().unwrap_or("ファイルシステムの操作を確認してください。"))]
    FileSystem {
        kind: FileSystemErrorKind,
        path: String,
        hint: Option<String>,
    },

    #[error("Dockerエラー\n{kind}\n内容: {message}\nヒント: {}", .hint.as_deref().unwrap_or("Docker環境を確認してください。"))]
    Docker {
        kind: DockerErrorKind,
        message: String,
        hint: Option<String>,
    },

    #[error("コンテストエラー\n{kind}\n内容: {message}\nヒント: {}", .hint.as_deref().unwrap_or("コンテストの設定を確認してください。"))]
    Contest {
        kind: ContestErrorKind,
        message: String,
        hint: Option<String>,
    },

    #[error("設定エラー\n{kind}\n内容: {message}\nヒント: {}", .hint.as_deref().unwrap_or("設定ファイルを確認してください。"))]
    Config {
        kind: ConfigErrorKind,
        message: String,
        hint: Option<String>,
    },

    #[error("{message}\nヒント: {}", .hint.as_deref().unwrap_or("詳細については、ドキュメントを参照してください。"))]
    Other {
        message: String,
        hint: Option<String>,
    },
}

#[derive(Debug, Clone)]
pub enum FileSystemErrorKind {
    NotFound,
    Permission,
    Io,
    Path,
}

impl std::fmt::Display for FileSystemErrorKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::NotFound => write!(f, "ファイルが見つかりません"),
            Self::Permission => write!(f, "アクセス権限がありません"),
            Self::Io => write!(f, "IOエラー"),
            Self::Path => write!(f, "パスエラー"),
        }
    }
}

#[derive(Debug, Clone)]
pub enum DockerErrorKind {
    ConnectionFailed,
    BuildFailed,
    ExecutionFailed,
    StateFailed,
}

impl std::fmt::Display for DockerErrorKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::ConnectionFailed => write!(f, "Dockerデーモンに接続できません"),
            Self::BuildFailed => write!(f, "イメージのビルドに失敗しました"),
            Self::ExecutionFailed => write!(f, "コンテナの実行に失敗しました"),
            Self::StateFailed => write!(f, "コンテナの状態管理に失敗しました"),
        }
    }
}

#[derive(Debug, Clone)]
pub enum ContestErrorKind {
    Site,
    Language,
    Compiler,
    State,
}

impl std::fmt::Display for ContestErrorKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Site => write!(f, "サイトエラー"),
            Self::Language => write!(f, "言語エラー"),
            Self::Compiler => write!(f, "コンパイラエラー"),
            Self::State => write!(f, "状態管理エラー"),
        }
    }
}

#[derive(Debug, Clone)]
pub enum ConfigErrorKind {
    NotFound,
    Parse,
    InvalidValue,
}

impl std::fmt::Display for ConfigErrorKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::NotFound => write!(f, "設定ファイルが見つかりません"),
            Self::Parse => write!(f, "設定ファイルの解析に失敗しました"),
            Self::InvalidValue => write!(f, "無効な設定値"),
        }
    }
}

/// エラーにコンテキストを追加するためのトレイト
pub trait ErrorExt {
    fn with_context(self, context: impl Into<String>) -> Self;
    fn with_hint(self, hint: impl Into<String>) -> Self;
}

impl ErrorExt for CphError {
    fn with_context(self, context: impl Into<String>) -> Self {
        match self {
            CphError::Docker { kind, message: _, hint } => {
                CphError::Docker {
                    kind,
                    message: context.into(),
                    hint,
                }
            }
            _ => self,
        }
    }

    fn with_hint(self, hint: impl Into<String>) -> Self {
        match self {
            CphError::FileSystem { kind, path, hint: _ } => {
                CphError::FileSystem {
                    kind,
                    path,
                    hint: Some(hint.into()),
                }
            }
            CphError::Docker { kind, message, hint: _ } => {
                CphError::Docker {
                    kind,
                    message,
                    hint: Some(hint.into()),
                }
            }
            CphError::Contest { kind, message, hint: _ } => {
                CphError::Contest {
                    kind,
                    message,
                    hint: Some(hint.into()),
                }
            }
            CphError::Config { kind, message, hint: _ } => {
                CphError::Config {
                    kind,
                    message,
                    hint: Some(hint.into()),
                }
            }
            CphError::Other { message, hint: _ } => {
                CphError::Other {
                    message,
                    hint: Some(hint.into()),
                }
            }
        }
    }
}

pub type Result<T> = std::result::Result<T, CphError>;

// エラーヘルパー関数
pub mod helpers {
    use super::*;

    // FileSystem
    pub fn fs_not_found(path: impl Into<String>) -> CphError {
        CphError::FileSystem {
            kind: FileSystemErrorKind::NotFound,
            path: path.into(),
            hint: None,
        }
    }

    pub fn fs_permission(path: impl Into<String>) -> CphError {
        CphError::FileSystem {
            kind: FileSystemErrorKind::Permission,
            path: path.into(),
            hint: None,
        }
    }

    pub fn fs_io(path: impl Into<String>, error: io::Error) -> CphError {
        CphError::FileSystem {
            kind: FileSystemErrorKind::Io,
            path: path.into(),
            hint: Some(error.to_string()),
        }
    }

    // Docker
    pub fn docker_connection() -> CphError {
        CphError::Docker {
            kind: DockerErrorKind::ConnectionFailed,
            message: "Dockerデーモンに接続できません".to_string(),
            hint: None,
        }
    }

    pub fn docker_build(message: impl Into<String>) -> CphError {
        CphError::Docker {
            kind: DockerErrorKind::BuildFailed,
            message: message.into(),
            hint: None,
        }
    }

    pub fn docker_execution(message: impl Into<String>) -> CphError {
        CphError::Docker {
            kind: DockerErrorKind::ExecutionFailed,
            message: message.into(),
            hint: None,
        }
    }

    // Contest
    pub fn contest_site(message: impl Into<String>) -> CphError {
        CphError::Contest {
            kind: ContestErrorKind::Site,
            message: message.into(),
            hint: None,
        }
    }

    pub fn contest_language(message: impl Into<String>) -> CphError {
        CphError::Contest {
            kind: ContestErrorKind::Language,
            message: message.into(),
            hint: None,
        }
    }

    pub fn contest_compiler(compiler: impl Into<String>) -> CphError {
        CphError::Contest {
            kind: ContestErrorKind::Compiler,
            message: format!("コンパイラが見つかりません: {}", compiler.into()),
            hint: None,
        }
    }

    // Config
    pub fn config_not_found(path: impl Into<String>) -> CphError {
        CphError::Config {
            kind: ConfigErrorKind::NotFound,
            message: format!("設定ファイルが見つかりません: {}", path.into()),
            hint: None,
        }
    }

    pub fn config_parse(error: impl std::error::Error) -> CphError {
        CphError::Config {
            kind: ConfigErrorKind::Parse,
            message: error.to_string(),
            hint: None,
        }
    }

    pub fn config_invalid(field: impl Into<String>, message: impl Into<String>) -> CphError {
        CphError::Config {
            kind: ConfigErrorKind::InvalidValue,
            message: format!("{}: {}", field.into(), message.into()),
            hint: None,
        }
    }
} 