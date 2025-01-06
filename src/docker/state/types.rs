use std::time::{Duration, Instant};
use thiserror::Error;

#[derive(Debug, Clone, PartialEq)]
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
        exit_code: i32,
        execution_time: Duration,
    },
    Failed {
        container_id: String,
        error: String,
        occurred_at: Instant,
    },
}

#[derive(Debug, Error)]
pub enum StateError {
    #[error("Invalid state transition from {from:?} to {to:?}")]
    InvalidTransition {
        from: ContainerState,
        to: ContainerState,
    },
    #[error("Container ID mismatch: expected {expected}, got {actual}")]
    ContainerIdMismatch {
        expected: String,
        actual: String,
    },
    #[error("Container not found: {0}")]
    ContainerNotFound(String),
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

    pub fn is_terminal(&self) -> bool {
        matches!(self, ContainerState::Stopped { .. } | ContainerState::Failed { .. })
    }

    pub fn duration_since_start(&self) -> Option<Duration> {
        match self {
            ContainerState::Running { started_at, .. } |
            ContainerState::Executing { started_at, .. } => Some(started_at.elapsed()),
            _ => None,
        }
    }
} 