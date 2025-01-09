use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ContainerStatus {
    Created,
    Starting,
    Running,
    Stopping,
    Stopped,
    Failed(String),
}

impl ContainerStatus {
    pub fn is_terminal(&self) -> bool {
        matches!(self, Self::Stopped | Self::Failed(_))
    }

    pub fn is_running(&self) -> bool {
        matches!(self, Self::Running)
    }
} 