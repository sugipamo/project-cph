use std::io;
use std::sync::Arc;
use thiserror::Error;

pub const NO_ACTIVE_CONTEST: &str = "アクティブなコンテストがありません。'work'コマンドで設定してください。";

/// エラーコンテキストを表す構造体
#[derive(Debug, Clone)]
pub struct ErrorContext {
    pub operation: String,
    pub location: String,
    pub hint: Option<String>,
    pub source: Option<Arc<dyn std::error::Error + Send + Sync>>,
}

impl ErrorContext {
    pub fn new(operation: impl Into<String>, location: impl Into<String>) -> Self {
        Self {
            operation: operation.into(),
            location: location.into(),
            hint: None,
            source: None,
        }
    }

    pub fn with_hint(mut self, hint: impl Into<String>) -> Self {
        self.hint = Some(hint.into());
        self
    }

    pub fn with_source(mut self, source: impl std::error::Error + Send + Sync + 'static) -> Self {
        self.source = Some(Arc::new(source));
        self
    }
}

/// 共通のエラー型
#[derive(Debug, Error)]
pub enum CphError {
    #[error("ファイルシステムエラー\n操作: {}\n場所: {}\nエラー: {}\nヒント: {}", 
        context.operation, context.location, 
        context.source.as_ref().map_or("不明".to_string(), |e| e.to_string()),
        context.hint.as_deref().unwrap_or("ファイルシステムの操作を確認してください。"))]
    FileSystem {
        context: ErrorContext,
        kind: FileSystemErrorKind,
    },

    #[error("Dockerエラー\n操作: {}\n場所: {}\nエラー: {}\nヒント: {}", 
        context.operation, context.location,
        context.source.as_ref().map_or("不明".to_string(), |e| e.to_string()),
        context.hint.as_deref().unwrap_or("Docker環境を確認してください。"))]
    Docker {
        context: ErrorContext,
        kind: DockerErrorKind,
    },

    #[error("コンテストエラー\n操作: {}\n場所: {}\nエラー: {}\nヒント: {}", 
        context.operation, context.location,
        context.source.as_ref().map_or("不明".to_string(), |e| e.to_string()),
        context.hint.as_deref().unwrap_or("コンテストの設定を確認してください。"))]
    Contest {
        context: ErrorContext,
        kind: ContestErrorKind,
    },

    #[error("設定エラー\n操作: {}\n場所: {}\nエラー: {}\nヒント: {}", 
        context.operation, context.location,
        context.source.as_ref().map_or("不明".to_string(), |e| e.to_string()),
        context.hint.as_deref().unwrap_or("設定ファイルを確認してください。"))]
    Config {
        context: ErrorContext,
        kind: ConfigErrorKind,
    },

    #[error("{}\nヒント: {}", 
        context.operation,
        context.hint.as_deref().unwrap_or("詳細については、ドキュメントを参照してください。"))]
    Other {
        context: ErrorContext,
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
    fn with_context(self, context: ErrorContext) -> Self;
    fn with_hint(self, hint: impl Into<String>) -> Self;
    fn with_source(self, source: impl std::error::Error + Send + Sync + 'static) -> Self;
}

impl ErrorExt for CphError {
    fn with_context(self, context: ErrorContext) -> Self {
        match self {
            CphError::FileSystem { kind, .. } => CphError::FileSystem { context, kind },
            CphError::Docker { kind, .. } => CphError::Docker { context, kind },
            CphError::Contest { kind, .. } => CphError::Contest { context, kind },
            CphError::Config { kind, .. } => CphError::Config { context, kind },
            CphError::Other { .. } => CphError::Other { context },
        }
    }

    fn with_hint(self, hint: impl Into<String>) -> Self {
        match self {
            CphError::FileSystem { context, kind } => {
                CphError::FileSystem {
                    context: context.with_hint(hint),
                    kind,
                }
            }
            CphError::Docker { context, kind } => {
                CphError::Docker {
                    context: context.with_hint(hint),
                    kind,
                }
            }
            CphError::Contest { context, kind } => {
                CphError::Contest {
                    context: context.with_hint(hint),
                    kind,
                }
            }
            CphError::Config { context, kind } => {
                CphError::Config {
                    context: context.with_hint(hint),
                    kind,
                }
            }
            CphError::Other { context } => {
                CphError::Other {
                    context: context.with_hint(hint),
                }
            }
        }
    }

    fn with_source(self, source: impl std::error::Error + Send + Sync + 'static) -> Self {
        match self {
            CphError::FileSystem { context, kind } => {
                CphError::FileSystem {
                    context: context.with_source(source),
                    kind,
                }
            }
            CphError::Docker { context, kind } => {
                CphError::Docker {
                    context: context.with_source(source),
                    kind,
                }
            }
            CphError::Contest { context, kind } => {
                CphError::Contest {
                    context: context.with_source(source),
                    kind,
                }
            }
            CphError::Config { context, kind } => {
                CphError::Config {
                    context: context.with_source(source),
                    kind,
                }
            }
            CphError::Other { context } => {
                CphError::Other {
                    context: context.with_source(source),
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
    pub fn fs_not_found(operation: impl Into<String>, path: impl Into<String>) -> CphError {
        CphError::FileSystem {
            context: ErrorContext::new(operation, path),
            kind: FileSystemErrorKind::NotFound,
        }
    }

    pub fn fs_permission(operation: impl Into<String>, path: impl Into<String>) -> CphError {
        CphError::FileSystem {
            context: ErrorContext::new(operation, path),
            kind: FileSystemErrorKind::Permission,
        }
    }

    pub fn fs_io(operation: impl Into<String>, path: impl Into<String>, error: io::Error) -> CphError {
        CphError::FileSystem {
            context: ErrorContext::new(operation, path).with_source(error),
            kind: FileSystemErrorKind::Io,
        }
    }

    // Docker
    pub fn docker_connection(operation: impl Into<String>) -> CphError {
        CphError::Docker {
            context: ErrorContext::new(operation, "Docker daemon"),
            kind: DockerErrorKind::ConnectionFailed,
        }
    }

    pub fn docker_build(operation: impl Into<String>, image: impl Into<String>, error: impl std::error::Error + Send + Sync + 'static) -> CphError {
        CphError::Docker {
            context: ErrorContext::new(operation, image).with_source(error),
            kind: DockerErrorKind::BuildFailed,
        }
    }

    pub fn docker_execution(operation: impl Into<String>, container: impl Into<String>, error: impl std::error::Error + Send + Sync + 'static) -> CphError {
        CphError::Docker {
            context: ErrorContext::new(operation, container).with_source(error),
            kind: DockerErrorKind::ExecutionFailed,
        }
    }

    // Contest
    pub fn contest_site(operation: impl Into<String>, site: impl Into<String>, error: impl std::error::Error + Send + Sync + 'static) -> CphError {
        CphError::Contest {
            context: ErrorContext::new(operation, site).with_source(error),
            kind: ContestErrorKind::Site,
        }
    }

    pub fn contest_language(operation: impl Into<String>, lang: impl Into<String>) -> CphError {
        CphError::Contest {
            context: ErrorContext::new(operation, lang),
            kind: ContestErrorKind::Language,
        }
    }

    pub fn contest_compiler(operation: impl Into<String>, compiler: impl Into<String>) -> CphError {
        CphError::Contest {
            context: ErrorContext::new(operation, compiler),
            kind: ContestErrorKind::Compiler,
        }
    }

    // Config
    pub fn config_not_found(operation: impl Into<String>, path: impl Into<String>) -> CphError {
        CphError::Config {
            context: ErrorContext::new(operation, path),
            kind: ConfigErrorKind::NotFound,
        }
    }

    pub fn config_parse(operation: impl Into<String>, path: impl Into<String>, error: impl std::error::Error + Send + Sync + 'static) -> CphError {
        CphError::Config {
            context: ErrorContext::new(operation, path).with_source(error),
            kind: ConfigErrorKind::Parse,
        }
    }

    pub fn config_invalid(operation: impl Into<String>, field: impl Into<String>, message: impl Into<String>) -> CphError {
        CphError::Config {
            context: ErrorContext::new(operation, field).with_hint(message),
            kind: ConfigErrorKind::InvalidValue,
        }
    }
} 