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

impl FileSystemErrorKind {
    pub fn hint(&self) -> &'static str {
        match self {
            Self::NotFound => "ファイルパスを確認してください",
            Self::Permission => "ファイルのアクセス権限を確認してください",
            Self::Io => "ファイルシステムの状態を確認してください",
            Self::Path => "パスの形式を確認してください",
            Self::Transaction => "トランザクションの整合性を確認してください",
        }
    }
} 