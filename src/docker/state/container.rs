use std::time::{Duration, Instant};
use tokio::sync::mpsc;
use thiserror::Error;
use std::sync::Arc;
use tokio::sync::Mutex;

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

pub struct ContainerStateManager {
    state: Arc<Mutex<ContainerState>>,
    container_id: Arc<Mutex<Option<String>>>,
    subscribers: Arc<Mutex<Vec<mpsc::Sender<ContainerState>>>>,
}

impl ContainerStateManager {
    pub fn new() -> Self {
        Self {
            state: Arc::new(Mutex::new(ContainerState::Initial)),
            container_id: Arc::new(Mutex::new(None)),
            subscribers: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub async fn set_container_id(&self, id: String) {
        let mut container_id = self.container_id.lock().await;
        *container_id = Some(id);
    }

    pub async fn get_container_id(&self) -> Option<String> {
        let container_id = self.container_id.lock().await;
        container_id.clone()
    }

    pub async fn transition_to(&self, new_state: ContainerState) -> Result<(), StateError> {
        let mut state = self.state.lock().await;
        
        // 状態遷移の検証
        self.validate_transition(&state, &new_state).await?;
        
        // 状態を更新
        *state = new_state.clone();
        
        // 購読者に通知
        self.notify_subscribers(new_state).await;
        
        Ok(())
    }

    async fn validate_transition(&self, current: &ContainerState, new: &ContainerState) -> Result<(), StateError> {
        match (current, new) {
            // 初期状態からの遷移
            (ContainerState::Initial, ContainerState::Created { .. }) => Ok(()),
            
            // Created状態からの遷移
            (ContainerState::Created { .. }, ContainerState::Running { .. }) |
            (ContainerState::Created { .. }, ContainerState::Failed { .. }) => {
                self.validate_container_id(current, new).await
            }
            
            // Running状態からの遷移
            (ContainerState::Running { .. }, ContainerState::Executing { .. }) |
            (ContainerState::Running { .. }, ContainerState::Stopped { .. }) |
            (ContainerState::Running { .. }, ContainerState::Failed { .. }) => {
                self.validate_container_id(current, new).await
            }
            
            // Executing状態からの遷移
            (ContainerState::Executing { .. }, ContainerState::Running { .. }) |
            (ContainerState::Executing { .. }, ContainerState::Stopped { .. }) |
            (ContainerState::Executing { .. }, ContainerState::Failed { .. }) => {
                self.validate_container_id(current, new).await
            }
            
            // 終端状態からの遷移は許可しない
            (ContainerState::Stopped { .. }, _) |
            (ContainerState::Failed { .. }, _) => {
                Err(StateError::InvalidTransition {
                    from: current.clone(),
                    to: new.clone(),
                })
            }
            
            // その他の遷移は無効
            _ => Err(StateError::InvalidTransition {
                from: current.clone(),
                to: new.clone(),
            }),
        }
    }

    async fn validate_container_id(&self, current: &ContainerState, new: &ContainerState) -> Result<(), StateError> {
        let current_id = current.container_id().unwrap_or_default();
        let new_id = new.container_id().unwrap_or_default();
        
        if current_id == new_id {
            Ok(())
        } else {
            Err(StateError::ContainerIdMismatch {
                expected: current_id.to_string(),
                actual: new_id.to_string(),
            })
        }
    }

    async fn notify_subscribers(&self, state: ContainerState) {
        let mut subscribers = self.subscribers.lock().await;
        subscribers.retain_mut(|subscriber| {
            subscriber.try_send(state.clone()).is_ok()
        });
    }

    pub async fn subscribe(&self) -> mpsc::Receiver<ContainerState> {
        let (tx, rx) = mpsc::channel(32);
        let mut subscribers = self.subscribers.lock().await;
        subscribers.push(tx);
        rx
    }

    pub async fn get_current_state(&self) -> ContainerState {
        let state = self.state.lock().await;
        state.clone()
    }
}

impl ContainerState {
    pub fn container_id(&self) -> Option<&str> {
        match self {
            ContainerState::Initial => None,
            ContainerState::Created { container_id, .. } => Some(container_id),
            ContainerState::Running { container_id, .. } => Some(container_id),
            ContainerState::Executing { container_id, .. } => Some(container_id),
            ContainerState::Stopped { container_id, .. } => Some(container_id),
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
            ContainerState::Stopped { execution_time, .. } => Some(*execution_time),
            _ => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_valid_state_transitions() {
        let manager = ContainerStateManager::new();
        
        // Initial -> Created
        let created_state = ContainerState::Created {
            container_id: "test_container".to_string(),
            created_at: Instant::now(),
        };
        assert!(manager.transition_to(created_state.clone()).await.is_ok());

        // Created -> Running
        let running_state = ContainerState::Running {
            container_id: "test_container".to_string(),
            started_at: Instant::now(),
        };
        assert!(manager.transition_to(running_state).await.is_ok());
    }

    #[tokio::test]
    async fn test_invalid_state_transitions() {
        let manager = ContainerStateManager::new();

        // Initial -> Running (invalid)
        let running_state = ContainerState::Running {
            container_id: "test_container".to_string(),
            started_at: Instant::now(),
        };
        assert!(manager.transition_to(running_state).await.is_err());
    }

    #[tokio::test]
    async fn test_container_id_mismatch() {
        let manager = ContainerStateManager::new();

        // Setup initial state
        let created_state = ContainerState::Created {
            container_id: "container1".to_string(),
            created_at: Instant::now(),
        };
        assert!(manager.transition_to(created_state).await.is_ok());

        // Try to transition with different container ID
        let running_state = ContainerState::Running {
            container_id: "container2".to_string(),
            started_at: Instant::now(),
        };
        assert!(matches!(
            manager.transition_to(running_state).await,
            Err(StateError::ContainerIdMismatch { .. })
        ));
    }

    #[tokio::test]
    async fn test_state_subscription() {
        let manager = ContainerStateManager::new();
        let mut rx = manager.subscribe().await;

        // Create state change
        let new_state = ContainerState::Created {
            container_id: "test_container".to_string(),
            created_at: Instant::now(),
        };
        manager.transition_to(new_state.clone()).await.unwrap();

        // Verify subscriber received the state
        let received_state = rx.recv().await.unwrap();
        assert_eq!(received_state, new_state);
    }
} 