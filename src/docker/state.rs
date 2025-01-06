use std::time::{Duration, Instant};
use tokio::sync::mpsc;
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
    Compiling {
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
    #[error("Internal state error: {0}")]
    Internal(String),
}

pub type StateResult<T> = Result<T, StateError>;

impl ContainerState {
    pub fn container_id(&self) -> Option<&str> {
        match self {
            ContainerState::Initial => None,
            ContainerState::Created { container_id, .. } => Some(container_id),
            ContainerState::Running { container_id, .. } => Some(container_id),
            ContainerState::Compiling { container_id, .. } => Some(container_id),
            ContainerState::Executing { container_id, .. } => Some(container_id),
            ContainerState::Stopped { container_id, .. } => Some(container_id),
            ContainerState::Failed { container_id, .. } => Some(container_id),
        }
    }

    pub fn is_terminal(&self) -> bool {
        matches!(
            self,
            ContainerState::Stopped { .. } | ContainerState::Failed { .. }
        )
    }

    pub fn duration_since_start(&self) -> Option<Duration> {
        match self {
            ContainerState::Running { started_at, .. }
            | ContainerState::Compiling { started_at, .. }
            | ContainerState::Executing { started_at, .. } => Some(started_at.elapsed()),
            ContainerState::Stopped { execution_time, .. } => Some(*execution_time),
            _ => None,
        }
    }
}

pub struct StateManager {
    current_state: ContainerState,
    subscribers: Vec<mpsc::Sender<ContainerState>>,
}

impl StateManager {
    pub fn new() -> Self {
        Self {
            current_state: ContainerState::Initial,
            subscribers: Vec::new(),
        }
    }

    pub async fn transition_to(&mut self, new_state: ContainerState) -> StateResult<()> {
        // 状態遷移の検証
        self.validate_transition(&new_state)?;

        // 状態を更新
        self.current_state = new_state.clone();

        // 購読者に通知
        self.notify_subscribers(new_state).await;

        Ok(())
    }

    fn validate_transition(&self, new_state: &ContainerState) -> StateResult<()> {
        use ContainerState::*;

        match (&self.current_state, new_state) {
            // 初期状態からの遷移
            (Initial, Created { .. }) => Ok(()),

            // Created状態からの遷移
            (Created { container_id, .. }, Running { container_id: new_id, .. })
            | (Created { container_id, .. }, Failed { container_id: new_id, .. }) => {
                if container_id == new_id {
                    Ok(())
                } else {
                    Err(StateError::ContainerIdMismatch {
                        expected: container_id.clone(),
                        actual: new_id.clone(),
                    })
                }
            }

            // Running状態からの遷移
            (Running { container_id, .. }, Compiling { container_id: new_id, .. })
            | (Running { container_id, .. }, Executing { container_id: new_id, .. })
            | (Running { container_id, .. }, Stopped { container_id: new_id, .. })
            | (Running { container_id, .. }, Failed { container_id: new_id, .. }) => {
                if container_id == new_id {
                    Ok(())
                } else {
                    Err(StateError::ContainerIdMismatch {
                        expected: container_id.clone(),
                        actual: new_id.clone(),
                    })
                }
            }

            // Compiling状態からの遷移
            (Compiling { container_id, .. }, Running { container_id: new_id, .. })
            | (Compiling { container_id, .. }, Failed { container_id: new_id, .. }) => {
                if container_id == new_id {
                    Ok(())
                } else {
                    Err(StateError::ContainerIdMismatch {
                        expected: container_id.clone(),
                        actual: new_id.clone(),
                    })
                }
            }

            // Executing状態からの遷移
            (Executing { container_id, .. }, Running { container_id: new_id, .. })
            | (Executing { container_id, .. }, Stopped { container_id: new_id, .. })
            | (Executing { container_id, .. }, Failed { container_id: new_id, .. }) => {
                if container_id == new_id {
                    Ok(())
                } else {
                    Err(StateError::ContainerIdMismatch {
                        expected: container_id.clone(),
                        actual: new_id.clone(),
                    })
                }
            }

            // 終端状態からの遷移は許可しない
            (Stopped { .. }, _) | (Failed { .. }, _) => {
                Err(StateError::InvalidTransition {
                    from: self.current_state.clone(),
                    to: new_state.clone(),
                })
            }

            // その他の遷移は無効
            _ => Err(StateError::InvalidTransition {
                from: self.current_state.clone(),
                to: new_state.clone(),
            }),
        }
    }

    async fn notify_subscribers(&mut self, state: ContainerState) {
        let mut closed_indices = Vec::new();

        for (i, subscriber) in self.subscribers.iter().enumerate() {
            if subscriber.send(state.clone()).await.is_err() {
                closed_indices.push(i);
            }
        }

        // クローズされた購読者を削除
        for i in closed_indices.iter().rev() {
            self.subscribers.remove(*i);
        }
    }

    pub async fn subscribe(&mut self) -> mpsc::Receiver<ContainerState> {
        let (tx, rx) = mpsc::channel(32);
        self.subscribers.push(tx);
        rx
    }

    pub fn get_current_state(&self) -> &ContainerState {
        &self.current_state
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_valid_state_transitions() {
        let mut manager = StateManager::new();
        
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
        let mut manager = StateManager::new();

        // Initial -> Running (invalid)
        let running_state = ContainerState::Running {
            container_id: "test_container".to_string(),
            started_at: Instant::now(),
        };
        assert!(manager.transition_to(running_state).await.is_err());
    }

    #[tokio::test]
    async fn test_container_id_mismatch() {
        let mut manager = StateManager::new();

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
        let mut manager = StateManager::new();
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