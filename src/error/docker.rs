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
            Self::ValidationFailed => write!(f, "コンテナの検証に失敗しました"),
        }
    }
}

impl DockerErrorKind {
    pub fn hint(&self) -> &'static str {
        match self {
            Self::ConnectionFailed => "Dockerデーモンが実行中か確認してください",
            Self::BuildFailed => "Dockerfileの内容を確認してください",
            Self::ExecutionFailed => "コンテナの実行パラメータを確認してください",
            Self::StateFailed => "コンテナの状態を確認してください",
            Self::ValidationFailed => "コンテナの設定を確認してください",
        }
    }
} 