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
            Self::Site => write!(f, "コンテストサイトエラー"),
            Self::Language => write!(f, "プログラミング言語エラー"),
            Self::Compiler => write!(f, "コンパイラエラー"),
            Self::State => write!(f, "コンテスト状態エラー"),
            Self::Parse => write!(f, "コンテスト情報の解析エラー"),
        }
    }
}

impl ContestErrorKind {
    pub fn hint(&self) -> &'static str {
        match self {
            Self::Site => "コンテストサイトの接続を確認してください",
            Self::Language => "対応言語リストを確認してください",
            Self::Compiler => "コンパイラの設定を確認してください",
            Self::State => "コンテストの状態を確認してください",
            Self::Parse => "コンテスト情報の形式を確認してください",
        }
    }
} 