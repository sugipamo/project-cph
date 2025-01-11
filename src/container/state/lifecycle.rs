use std::fmt;
use anyhow::Result;
use serde::{Serialize, Deserialize};

/// コンテナの状態を表す列挙型
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Status {
    /// 作成済み
    Created,
    /// 起動中
    Starting,
    /// 実行中
    Running,
    /// 停止中
    Stopping,
    /// 停止済み
    Stopped,
    /// エラーで失敗
    Failed(String),
}

impl Default for Status {
    fn default() -> Self {
        Self::Created
    }
}

impl fmt::Display for Status {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Created => write!(f, "Created"),
            Self::Starting => write!(f, "Starting"),
            Self::Running => write!(f, "Running"),
            Self::Stopping => write!(f, "Stopping"),
            Self::Stopped => write!(f, "Stopped"),
            Self::Failed(reason) => write!(f, "Failed: {reason}"),
        }
    }
}

impl Status {
    /// 状態が終了状態かどうかを返します
    #[must_use]
    pub const fn is_terminal(&self) -> bool {
        matches!(self, Self::Stopped | Self::Failed(_))
    }

    /// 状態が実行中かどうかを返します
    #[must_use]
    pub const fn is_running(&self) -> bool {
        matches!(self, Self::Running)
    }

    /// 指定された状態に遷移できるかどうかを確認し、遷移します
    ///
    /// # Errors
    /// - 無効な状態遷移が要求された場合
    pub fn transition_to(&self, target: Self) -> Result<Self> {
        if self.can_transition_to(&target) {
            Ok(target)
        } else {
            Err(anyhow::anyhow!(
                "無効な状態遷移です: {} -> {}",
                self,
                target
            ))
        }
    }

    const fn can_transition_to(&self, target: &Self) -> bool {
        use Status::{Created, Failed, Running, Starting, Stopped, Stopping};
        match (self, target) {
            // 正常な状態遷移パス
            (Created | Starting | Running | Stopping, Failed(_)) |
            (Created, Starting) |
            (Starting, Running) |
            (Running, Stopping) |
            (Stopping, Stopped) => true,
            // その他の遷移は無効
            _ => false,
        }
    }
} 