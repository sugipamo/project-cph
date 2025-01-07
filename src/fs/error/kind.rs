use std::fmt;
use crate::error::ErrorSeverity;

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
    Path,
    /// トランザクション処理に失敗
    Transaction,
}

impl FileSystemErrorKind {
    /// エラーの重大度を返します
    pub fn severity(&self) -> ErrorSeverity {
        match self {
            Self::NotFound => ErrorSeverity::Warning,
            Self::Permission => ErrorSeverity::Error,
            Self::Io => ErrorSeverity::Error,
            Self::Path => ErrorSeverity::Warning,
            Self::Transaction => ErrorSeverity::Error,
        }
    }

    /// エラーのデフォルトのヒントメッセージを返します
    pub fn hint(&self) -> &'static str {
        match self {
            Self::NotFound => "ファイルまたはディレクトリの存在を確認してください。",
            Self::Permission => "必要な権限があるか確認してください。",
            Self::Io => "ディスクの空き容量やファイルの状態を確認してください。",
            Self::Path => "パスの形式が正しいか確認してください。",
            Self::Transaction => "操作をやり直してください。",
        }
    }
}

impl fmt::Display for FileSystemErrorKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotFound => write!(f, "ファイルが見つかりません"),
            Self::Permission => write!(f, "アクセス権限がありません"),
            Self::Io => write!(f, "IOエラー"),
            Self::Path => write!(f, "パスエラー"),
            Self::Transaction => write!(f, "トランザクションエラー"),
        }
    }
} 