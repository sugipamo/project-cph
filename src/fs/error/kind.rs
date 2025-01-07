use std::fmt;
use crate::error::{ErrorKind, ErrorSeverity};

/// ファイルシステムエラーの種類を表す列挙型
#[derive(Debug, Clone)]
pub enum FileSystemErrorKind {
    /// ファイルまたはディレクトリが見つからない
    NotFound,
    /// アクセス権限がない
    Permission,
    /// I/O操作に失敗
    Io,
    /// パスの操作に失敗
    InvalidPath,
    /// トランザクション処理に失敗
    Transaction,
    /// バックアップ操作に失敗
    Backup,
    /// 検証エラー
    Validation,
    /// その他のエラー
    Other(String),
}

impl ErrorKind for FileSystemErrorKind {
    fn severity(&self) -> ErrorSeverity {
        match self {
            Self::NotFound | Self::InvalidPath => ErrorSeverity::Warning,
            Self::Permission | Self::Io | Self::Transaction | Self::Backup => ErrorSeverity::Error,
            Self::Validation | Self::Other(_) => ErrorSeverity::Warning,
        }
    }
}

impl fmt::Display for FileSystemErrorKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotFound => write!(f, "ファイルが見つかりません"),
            Self::Permission => write!(f, "アクセス権限がありません"),
            Self::Io => write!(f, "IOエラー"),
            Self::InvalidPath => write!(f, "無効なパス"),
            Self::Transaction => write!(f, "トランザクションエラー"),
            Self::Backup => write!(f, "バックアップエラー"),
            Self::Validation => write!(f, "検証エラー"),
            Self::Other(s) => write!(f, "{}", s),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_kind_severity() {
        assert_eq!(FileSystemErrorKind::NotFound.severity(), ErrorSeverity::Warning);
        assert_eq!(FileSystemErrorKind::Permission.severity(), ErrorSeverity::Error);
        assert_eq!(FileSystemErrorKind::Io.severity(), ErrorSeverity::Error);
        assert_eq!(FileSystemErrorKind::InvalidPath.severity(), ErrorSeverity::Warning);
        assert_eq!(FileSystemErrorKind::Transaction.severity(), ErrorSeverity::Error);
        assert_eq!(FileSystemErrorKind::Backup.severity(), ErrorSeverity::Error);
        assert_eq!(FileSystemErrorKind::Validation.severity(), ErrorSeverity::Warning);
        assert_eq!(FileSystemErrorKind::Other("test".to_string()).severity(), ErrorSeverity::Warning);
    }

    #[test]
    fn test_error_kind_display() {
        assert_eq!(FileSystemErrorKind::NotFound.to_string(), "ファイルが見つかりません");
        assert_eq!(FileSystemErrorKind::Permission.to_string(), "アクセス権限がありません");
        assert_eq!(FileSystemErrorKind::Io.to_string(), "IOエラー");
        assert_eq!(FileSystemErrorKind::InvalidPath.to_string(), "無効なパス");
        assert_eq!(FileSystemErrorKind::Transaction.to_string(), "トランザクションエラー");
        assert_eq!(FileSystemErrorKind::Backup.to_string(), "バックアップエラー");
        assert_eq!(FileSystemErrorKind::Validation.to_string(), "検証エラー");
        assert_eq!(FileSystemErrorKind::Other("test".to_string()).to_string(), "test");
    }
} 