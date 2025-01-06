use crate::error::{CphError, ErrorContext, ErrorSeverity};
use crate::error::fs::FileSystemErrorKind;
use crate::error::docker::DockerErrorKind;
use crate::error::contest::ContestErrorKind;
use crate::error::config::ConfigErrorKind;

// ファイルシステム関連のヘルパー関数
pub fn fs_error(kind: FileSystemErrorKind, op: impl Into<String>, path: impl Into<String>) -> CphError {
    CphError::FileSystem {
        context: ErrorContext::new(op, path).with_severity(match kind {
            FileSystemErrorKind::NotFound => ErrorSeverity::Warning,
            FileSystemErrorKind::Permission => ErrorSeverity::Error,
            FileSystemErrorKind::Io => ErrorSeverity::Error,
            FileSystemErrorKind::Path => ErrorSeverity::Warning,
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