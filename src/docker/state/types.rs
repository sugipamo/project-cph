use std::fmt;
use std::time::{Duration, Instant};
use std::process::ExitStatus;
use std::sync::Arc;

#[derive(Debug, Clone)]
pub enum StateType {
    Running,
    Executing(Arc<String>),
    Stopped,
    Failed(Arc<String>),
}

#[derive(Debug, Clone)]
pub struct StateInfo {
    pub container_id: Arc<String>,
    pub state_type: StateType,
    pub timestamp: Arc<Instant>,
}

#[derive(Debug, Clone)]
pub enum ContainerState {
    Initial,
    Created {
        container_id: Arc<String>,
        created_at: Arc<Instant>,
    },
    Running {
        container_id: Arc<String>,
        started_at: Arc<Instant>,
    },
    Executing {
        container_id: Arc<String>,
        started_at: Arc<Instant>,
        command: Arc<String>,
    },
    Stopped {
        container_id: Arc<String>,
        stopped_at: Arc<Instant>,
        exit_status: Option<Arc<ExitStatus>>,
    },
    Failed {
        container_id: Arc<String>,
        error: Arc<String>,
        occurred_at: Arc<Instant>,
    },
}

impl ContainerState {
    pub fn new() -> Self {
        Self::Initial
    }

    pub fn create(container_id: String) -> Self {
        Self::Created {
            container_id: Arc::new(container_id),
            created_at: Arc::new(Instant::now()),
        }
    }

    pub fn start(&self) -> Option<Self> {
        match self {
            Self::Created { container_id, .. } => Some(Self::Running {
                container_id: Arc::clone(container_id),
                started_at: Arc::new(Instant::now()),
            }),
            _ => None,
        }
    }

    pub fn execute(&self, command: String) -> Option<Self> {
        match self {
            Self::Running { container_id, started_at } => Some(Self::Executing {
                container_id: Arc::clone(container_id),
                started_at: Arc::clone(started_at),
                command: Arc::new(command),
            }),
            _ => None,
        }
    }

    pub fn stop(&self) -> Option<Self> {
        match self {
            Self::Running { container_id, .. } |
            Self::Executing { container_id, .. } => Some(Self::Stopped {
                container_id: Arc::clone(container_id),
                stopped_at: Arc::new(Instant::now()),
                exit_status: None,
            }),
            _ => None,
        }
    }

    pub fn fail(&self, error: String) -> Option<Self> {
        match self {
            Self::Created { container_id, .. } |
            Self::Running { container_id, .. } |
            Self::Executing { container_id, .. } => Some(Self::Failed {
                container_id: Arc::clone(container_id),
                error: Arc::new(error),
                occurred_at: Arc::new(Instant::now()),
            }),
            _ => None,
        }
    }

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

    pub fn regenerate(&self) -> Option<Self> {
        self.get_container_id_for_regeneration()
            .map(|container_id| Self::Created {
                container_id: Arc::clone(container_id),
                created_at: Arc::new(Instant::now()),
            })
    }

    fn get_container_id_for_regeneration(&self) -> Option<&Arc<String>> {
        match self {
            Self::Running { container_id, .. } |
            Self::Executing { container_id, .. } |
            Self::Stopped { container_id, .. } |
            Self::Failed { container_id, .. } => Some(container_id),
            _ => None,
        }
    }

    pub fn can_regenerate(&self) -> bool {
        self.get_container_id_for_regeneration().is_some()
    }

    pub fn get_state_info(&self) -> Option<StateInfo> {
        self.create_state_info()
    }

    fn create_state_info(&self) -> Option<StateInfo> {
        match self {
            Self::Running { container_id, started_at } => Some(StateInfo {
                container_id: Arc::clone(container_id),
                state_type: StateType::Running,
                timestamp: Arc::clone(started_at),
            }),
            Self::Executing { container_id, started_at, command } => Some(StateInfo {
                container_id: Arc::clone(container_id),
                state_type: StateType::Executing(Arc::clone(command)),
                timestamp: Arc::clone(started_at),
            }),
            Self::Stopped { container_id, stopped_at, .. } => Some(StateInfo {
                container_id: Arc::clone(container_id),
                state_type: StateType::Stopped,
                timestamp: Arc::clone(stopped_at),
            }),
            Self::Failed { container_id, occurred_at, error } => Some(StateInfo {
                container_id: Arc::clone(container_id),
                state_type: StateType::Failed(Arc::clone(error)),
                timestamp: Arc::clone(occurred_at),
            }),
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