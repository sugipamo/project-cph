use serde::{Serialize, Deserialize};
use anyhow::{Result, anyhow};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ContainerStatus {
    Created,
    Starting,
    Running,
    Stopping,
    Stopped,
    Failed(String),
}

impl std::fmt::Display for ContainerStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Created => write!(f, "Created"),
            Self::Starting => write!(f, "Starting"),
            Self::Running => write!(f, "Running"),
            Self::Stopping => write!(f, "Stopping"),
            Self::Stopped => write!(f, "Stopped"),
            Self::Failed(reason) => write!(f, "Failed: {}", reason),
        }
    }
}

impl ContainerStatus {
    pub fn is_terminal(&self) -> bool {
        matches!(self, Self::Stopped | Self::Failed(_))
    }

    pub fn is_running(&self) -> bool {
        matches!(self, Self::Running)
    }

    pub fn transition_to(&self, target: ContainerStatus) -> Result<ContainerStatus> {
        if self.can_transition_to(&target) {
            Ok(target)
        } else {
            Err(anyhow!("不正な状態遷移です: {} -> {}", self, target))
        }
    }

    fn can_transition_to(&self, target: &ContainerStatus) -> bool {
        use ContainerStatus::*;
        match (self, target) {
            // 正常な状態遷移パス
            (Created, Starting) => true,
            (Starting, Running) => true,
            (Running, Stopping) => true,
            (Stopping, Stopped) => true,
            // 異常系への遷移は常に許可
            (_, Failed(_)) => true,
            // その他の遷移は不許可
            _ => false,
        }
    }
} 