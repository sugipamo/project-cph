#[macro_use]
pub mod macros;

use std::sync::Arc;
use thiserror::Error;

pub const NO_ACTIVE_CONTEST: &str = "アクティブなコンテストがありません。'work'コマンドで設定してください。";

// サブモジュールの定義
pub mod fs;
pub mod docker;
pub mod contest;
pub mod config;

/// エラーの重大度を表す列挙型
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ErrorSeverity {
    Info,
    Warning,
    Error,
    Critical,
}

impl Default for ErrorSeverity {
    fn default() -> Self {
        Self::Error
    }
}

/// エラーコンテキストを表す構造体
#[derive(Debug, Clone)]
pub struct ErrorContext {
    pub operation: String,
    pub location: String,
    pub hint: Option<String>,
    pub source: Option<Arc<dyn std::error::Error + Send + Sync>>,
    pub backtrace: Option<String>,
    pub system_state: Option<SystemState>,
    pub severity: ErrorSeverity,
}

/// システム状態を表す構造体
#[derive(Debug, Clone)]
pub struct SystemState {
    pub working_directory: String,
    pub active_contest: Option<String>,
    pub docker_status: Option<String>,
    pub last_operation: Option<String>,
    pub environment_info: Option<String>,
}

impl Default for ErrorContext {
    fn default() -> Self {
        Self {
            operation: String::new(),
            location: String::new(),
            hint: None,
            source: None,
            backtrace: None,
            system_state: None,
            severity: ErrorSeverity::default(),
        }
    }
}

impl ErrorContext {
    pub fn new(operation: impl Into<String>, location: impl Into<String>) -> Self {
        Self {
            operation: operation.into(),
            location: location.into(),
            hint: None,
            source: None,
            backtrace: None,
            system_state: None,
            severity: ErrorSeverity::default(),
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

    pub fn with_system_state(mut self, state: SystemState) -> Self {
        self.system_state = Some(state);
        self
    }

    pub fn with_severity(mut self, severity: ErrorSeverity) -> Self {
        self.severity = severity;
        self
    }
}

/// 共通のエラー型
#[derive(Debug, Error)]
pub enum CphError {
    #[error("{}\n場所: {}\n重大度: {:?}\nエラー: {}\nヒント: {}", 
        context.operation,
        context.location,
        context.severity,
        context.source.as_ref().map_or("不明".to_string(), |e| e.to_string()),
        context.hint.as_deref().unwrap_or("詳細については、ドキュメントを参照してください。"))]
    FileSystem {
        context: ErrorContext,
        kind: fs::FileSystemErrorKind,
    },

    #[error("{}\n場所: {}\n重大度: {:?}\nエラー: {}\nヒント: {}", 
        context.operation,
        context.location,
        context.severity,
        context.source.as_ref().map_or("不明".to_string(), |e| e.to_string()),
        context.hint.as_deref().unwrap_or("Dockerの設定を確認してください。"))]
    Docker {
        context: ErrorContext,
        kind: docker::DockerErrorKind,
    },

    #[error("{}\n場所: {}\n重大度: {:?}\nエラー: {}\nヒント: {}", 
        context.operation,
        context.location,
        context.severity,
        context.source.as_ref().map_or("不明".to_string(), |e| e.to_string()),
        context.hint.as_deref().unwrap_or("コンテストの設定を確認してください。"))]
    Contest {
        context: ErrorContext,
        kind: contest::ContestErrorKind,
    },

    #[error("{}\n場所: {}\n重大度: {:?}\nエラー: {}\nヒント: {}", 
        context.operation,
        context.location,
        context.severity,
        context.source.as_ref().map_or("不明".to_string(), |e| e.to_string()),
        context.hint.as_deref().unwrap_or("設定ファイルを確認してください。"))]
    Config {
        context: ErrorContext,
        kind: config::ConfigErrorKind,
    },

    #[error("{}\n場所: {}\n重大度: {:?}\nヒント: {}", 
        context.operation,
        context.location,
        context.severity,
        context.hint.as_deref().unwrap_or("詳細については、ドキュメントを参照してください。"))]
    Other {
        context: ErrorContext,
    },
}

/// エラーにコンテキストを追加するためのトレイト
pub trait ErrorExt {
    fn with_context(self, context: ErrorContext) -> Self;
    fn with_hint(self, hint: impl Into<String>) -> Self;
    fn with_source(self, source: impl std::error::Error + Send + Sync + 'static) -> Self;
    fn with_severity(self, severity: ErrorSeverity) -> Self;
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

    fn with_severity(self, severity: ErrorSeverity) -> Self {
        match self {
            CphError::FileSystem { context, kind } => {
                CphError::FileSystem {
                    context: context.with_severity(severity),
                    kind,
                }
            }
            CphError::Docker { context, kind } => {
                CphError::Docker {
                    context: context.with_severity(severity),
                    kind,
                }
            }
            CphError::Contest { context, kind } => {
                CphError::Contest {
                    context: context.with_severity(severity),
                    kind,
                }
            }
            CphError::Config { context, kind } => {
                CphError::Config {
                    context: context.with_severity(severity),
                    kind,
                }
            }
            CphError::Other { context } => {
                CphError::Other {
                    context: context.with_severity(severity),
                }
            }
        }
    }
}

#[derive(Debug, Clone)]
pub enum FileSystemErrorKind {
    NotFound,
    Permission,
    Io,
    Path,
    Transaction,
}

impl std::fmt::Display for FileSystemErrorKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::NotFound => write!(f, "ファイルが見つかりません"),
            Self::Permission => write!(f, "アクセス権限がありません"),
            Self::Io => write!(f, "IOエラー"),
            Self::Path => write!(f, "パスエラー"),
            Self::Transaction => write!(f, "トランザクションエラー"),
        }
    }
}

#[derive(Debug, Clone)]
pub enum DockerErrorKind {
    ConnectionFailed,
    BuildFailed,
    ExecutionFailed,
    StateFailed,
    ValidationFailed,
}

impl std::fmt::Display for DockerErrorKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::ConnectionFailed => write!(f, "Dockerデーモンに接続できません"),
            Self::BuildFailed => write!(f, "イメージのビルドに失敗しました"),
            Self::ExecutionFailed => write!(f, "コンテナの実行に失敗しました"),
            Self::StateFailed => write!(f, "コンテナの状態管理に失敗しました"),
            Self::ValidationFailed => write!(f, "バリデーションエラー"),
        }
    }
}

#[derive(Debug, Clone)]
pub enum ContestErrorKind {
    Site,
    Language,
    Compiler,
    State,
    Parse,
}

impl std::fmt::Display for ContestErrorKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Site => write!(f, "サイトエラー"),
            Self::Language => write!(f, "言語エラー"),
            Self::Compiler => write!(f, "コンパイラエラー"),
            Self::State => write!(f, "状態管理エラー"),
            Self::Parse => write!(f, "パースエラー"),
        }
    }
}

#[derive(Debug, Clone)]
pub enum ConfigErrorKind {
    NotFound,
    Parse,
    InvalidValue,
    Validation,
}

impl std::fmt::Display for ConfigErrorKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::NotFound => write!(f, "設定ファイルが見つかりません"),
            Self::Parse => write!(f, "設定ファイルの解析に失敗しました"),
            Self::InvalidValue => write!(f, "無効な設定値"),
            Self::Validation => write!(f, "バリデーションエラー"),
        }
    }
}

pub type Result<T> = std::result::Result<T, CphError>;

// エラーヘルパー関数
pub mod helpers {
    use super::*;
    use super::fs::FileSystemErrorKind;
    use super::docker::DockerErrorKind;
    use super::contest::ContestErrorKind;
    use super::config::ConfigErrorKind;

    // ファイルシステム関連のヘルパー関数
    pub fn fs_error(kind: FileSystemErrorKind, op: impl Into<String>, path: impl Into<String>) -> CphError {
        CphError::FileSystem {
            context: ErrorContext::new(op, path).with_severity(match kind {
                FileSystemErrorKind::NotFound => ErrorSeverity::Warning,
                FileSystemErrorKind::Permission => ErrorSeverity::Error,
                FileSystemErrorKind::Io => ErrorSeverity::Error,
                FileSystemErrorKind::Path => ErrorSeverity::Warning,
                FileSystemErrorKind::Transaction => ErrorSeverity::Error,
            }),
            kind,
        }
    }

    // Docker関連のヘルパー関数
    pub fn docker_error(kind: DockerErrorKind, op: impl Into<String>, context: impl Into<String>) -> CphError {
        CphError::Docker {
            context: ErrorContext::new(op, context).with_severity(match kind {
                DockerErrorKind::ConnectionFailed => ErrorSeverity::Critical,
                DockerErrorKind::BuildFailed => ErrorSeverity::Error,
                DockerErrorKind::ExecutionFailed => ErrorSeverity::Error,
                DockerErrorKind::StateFailed => ErrorSeverity::Warning,
                DockerErrorKind::ValidationFailed => ErrorSeverity::Error,
            }),
            kind,
        }
    }

    // コンテスト関連のヘルパー関数
    pub fn contest_error(kind: ContestErrorKind, op: impl Into<String>, context: impl Into<String>) -> CphError {
        CphError::Contest {
            context: ErrorContext::new(op, context).with_severity(match kind {
                ContestErrorKind::Site => ErrorSeverity::Error,
                ContestErrorKind::Language => ErrorSeverity::Warning,
                ContestErrorKind::Compiler => ErrorSeverity::Error,
                ContestErrorKind::State => ErrorSeverity::Warning,
                ContestErrorKind::Parse => ErrorSeverity::Error,
            }),
            kind,
        }
    }

    // 設定関連のヘルパー関数
    pub fn config_error(kind: ConfigErrorKind, op: impl Into<String>, context: impl Into<String>) -> CphError {
        CphError::Config {
            context: ErrorContext::new(op, context).with_severity(match kind {
                ConfigErrorKind::NotFound => ErrorSeverity::Warning,
                ConfigErrorKind::Parse => ErrorSeverity::Error,
                ConfigErrorKind::InvalidValue => ErrorSeverity::Error,
                ConfigErrorKind::Validation => ErrorSeverity::Error,
            }),
            kind,
        }
    }

    // 一般的なエラーヘルパー関数
    pub fn other_error(op: impl Into<String>, context: impl Into<String>, severity: ErrorSeverity) -> CphError {
        CphError::Other {
            context: ErrorContext::new(op, context).with_severity(severity),
        }
    }

    // バックトレース付きのエラーコンテキスト生成
    pub fn with_backtrace(mut context: ErrorContext) -> ErrorContext {
        if context.backtrace.is_none() {
            context.backtrace = Some(std::backtrace::Backtrace::capture().to_string());
        }
        context
    }
}

// エラー変換マクロ
#[macro_export]
macro_rules! into_cph_error {
    ($operation:expr, $location:expr, $error:expr) => {
        match $error {
            err @ std::io::Error { .. } => {
                crate::error::helpers::fs_io($operation, $location, err)
            }
            err => CphError::Other {
                context: ErrorContext::new($operation, $location).with_source(err),
            },
        }
    };
} 