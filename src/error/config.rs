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
            Self::Validation => write!(f, "設定値の検証に失敗しました"),
        }
    }
}

impl ConfigErrorKind {
    pub fn hint(&self) -> &'static str {
        match self {
            Self::NotFound => "設定ファイルの場所を確認してください",
            Self::Parse => "設定ファイルの形式を確認してください",
            Self::InvalidValue => "設定値の範囲や形式を確認してください",
            Self::Validation => "設定値の組み合わせを確認してください",
        }
    }
} 