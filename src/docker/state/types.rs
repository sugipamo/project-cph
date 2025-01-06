use std::fmt;
use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub enum ContainerState {
    Initial,
    Created {
        container_id: String,
        created_at: Instant,
    },
    Running {
        container_id: String,
        started_at: Instant,
    },
    Executing {
        container_id: String,
        started_at: Instant,
        command: String,
    },
    Stopped {
        container_id: String,
        stopped_at: Instant,
        exit_status: Option<ExitStatus>,
    },
    Failed {
        container_id: String,
        error: String,
        occurred_at: Instant,
    },
}

impl ContainerState {
    pub fn container_id(&self) -> Option<&str> {
        match self {
            ContainerState::Initial => None,
            ContainerState::Created { container_id, .. } |
            ContainerState::Running { container_id, .. } |
            ContainerState::Executing { container_id, .. } |
            ContainerState::Stopped { container_id, .. } |
            ContainerState::Failed { container_id, .. } => Some(container_id),
        }
    }

    pub fn duration_since_start(&self) -> Option<Duration> {
        match self {
            ContainerState::Running { started_at, .. } |
            ContainerState::Executing { started_at, .. } => {
                Some(started_at.elapsed())
            }
            _ => None,
        }
    }
}

impl fmt::Display for ContainerState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ContainerState::Initial => write!(f, "初期状態"),
            ContainerState::Created { container_id, .. } => {
                write!(f, "作成済み(ID: {})", container_id)
            }
            ContainerState::Running { container_id, .. } => {
                write!(f, "実行中(ID: {})", container_id)
            }
            ContainerState::Executing { container_id, command, .. } => {
                write!(f, "コマンド実行中(ID: {}, コマンド: {})", container_id, command)
            }
            ContainerState::Stopped { container_id, .. } => {
                write!(f, "停止済み(ID: {})", container_id)
            }
            ContainerState::Failed { container_id, error, .. } => {
                write!(f, "失敗(ID: {}, エラー: {})", container_id, error)
            }
        }
    }
} 