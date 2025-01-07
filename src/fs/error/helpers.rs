use crate::error::{CphError, ErrorContext};
use super::FileSystemErrorKind;

/// ファイルが見つからない場合のエラーを作成します
pub fn not_found_err(path: impl Into<String>) -> CphError {
    CphError::FileSystem {
        context: ErrorContext::new("ファイル検索", path.into())
            .with_hint(FileSystemErrorKind::NotFound.hint())
            .with_severity(FileSystemErrorKind::NotFound.severity()),
        kind: FileSystemErrorKind::NotFound,
    }
}

/// I/Oエラーを作成します
pub fn io_err(error: std::io::Error, context: impl Into<String>) -> CphError {
    CphError::FileSystem {
        context: ErrorContext::new("ファイル操作", context.into())
            .with_hint(FileSystemErrorKind::Io.hint())
            .with_severity(FileSystemErrorKind::Io.severity())
            .with_source(error),
        kind: FileSystemErrorKind::Io,
    }
}

/// アクセス権限エラーを作成します
pub fn permission_err(path: impl Into<String>) -> CphError {
    CphError::FileSystem {
        context: ErrorContext::new("ファイルアクセス", path.into())
            .with_hint(FileSystemErrorKind::Permission.hint())
            .with_severity(FileSystemErrorKind::Permission.severity()),
        kind: FileSystemErrorKind::Permission,
    }
}

/// トランザクションエラーを作成します
pub fn transaction_err(error: std::io::Error, context: impl Into<String>) -> CphError {
    CphError::FileSystem {
        context: ErrorContext::new("トランザクション処理", context.into())
            .with_hint(FileSystemErrorKind::Transaction.hint())
            .with_severity(FileSystemErrorKind::Transaction.severity())
            .with_source(error),
        kind: FileSystemErrorKind::Transaction,
    }
}

/// パスエラーを作成します
pub fn path_err(path: impl Into<String>) -> CphError {
    CphError::FileSystem {
        context: ErrorContext::new("パス解決", path.into())
            .with_hint(FileSystemErrorKind::Path.hint())
            .with_severity(FileSystemErrorKind::Path.severity()),
        kind: FileSystemErrorKind::Path,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{Error, ErrorKind};

    #[test]
    fn test_helper_functions() {
        let not_found = not_found_err("test.txt");
        if let CphError::FileSystem { context, kind } = not_found {
            assert_eq!(context.operation, "ファイル検索");
            assert_eq!(context.location, "test.txt");
            assert!(matches!(kind, FileSystemErrorKind::NotFound));
        } else {
            panic!("Expected FileSystem error");
        }

        let error = Error::new(ErrorKind::Other, "test error");
        let io = io_err(error, "test.txt");
        if let CphError::FileSystem { context, kind } = io {
            assert_eq!(context.operation, "ファイル操作");
            assert_eq!(context.location, "test.txt");
            assert!(matches!(kind, FileSystemErrorKind::Io));
        } else {
            panic!("Expected FileSystem error");
        }
    }
} 