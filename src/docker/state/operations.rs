use std::time::Instant;
use crate::docker::state::types::{ContainerState, StateError};
use crate::docker::state::manager::ContainerStateManager;

impl ContainerStateManager {
    pub async fn create_container(&self, container_id: String) -> Result<(), StateError> {
        let current_state = self.get_current_state().await;
        match current_state {
            ContainerState::Initial => {
                self.transition_to(ContainerState::Created {
                    container_id,
                    created_at: Instant::now(),
                }).await
            },
            _ => Err(StateError::InvalidTransition {
                from: current_state,
                to: ContainerState::Created {
                    container_id,
                    created_at: Instant::now(),
                },
            }),
        }
    }

    pub async fn start_container(&self, container_id: String) -> Result<(), StateError> {
        let current_state = self.get_current_state().await;
        match current_state {
            ContainerState::Created { container_id: current_id, .. } if current_id == container_id => {
                self.transition_to(ContainerState::Running {
                    container_id,
                    started_at: Instant::now(),
                }).await
            },
            _ => Err(StateError::InvalidTransition {
                from: current_state,
                to: ContainerState::Running {
                    container_id,
                    started_at: Instant::now(),
                },
            }),
        }
    }

    pub async fn execute_command(&self, container_id: String, command: String) -> Result<(), StateError> {
        let current_state = self.get_current_state().await;
        match current_state {
            ContainerState::Running { container_id: current_id, .. } if current_id == container_id => {
                self.transition_to(ContainerState::Executing {
                    container_id,
                    started_at: Instant::now(),
                    command,
                }).await
            },
            _ => Err(StateError::InvalidTransition {
                from: current_state,
                to: ContainerState::Executing {
                    container_id,
                    started_at: Instant::now(),
                    command,
                },
            }),
        }
    }

    pub async fn stop_container(&self, container_id: String, exit_code: i32) -> Result<(), StateError> {
        let current_state = self.get_current_state().await;
        let execution_time = current_state.duration_since_start()
            .ok_or_else(|| StateError::InvalidTransition {
                from: current_state.clone(),
                to: ContainerState::Stopped {
                    container_id: container_id.clone(),
                    exit_code,
                    execution_time: std::time::Duration::from_secs(0),
                },
            })?;

        match current_state {
            ContainerState::Running { container_id: current_id, .. } |
            ContainerState::Executing { container_id: current_id, .. }
                if current_id == container_id => {
                self.transition_to(ContainerState::Stopped {
                    container_id,
                    exit_code,
                    execution_time,
                }).await
            },
            _ => Err(StateError::InvalidTransition {
                from: current_state,
                to: ContainerState::Stopped {
                    container_id,
                    exit_code,
                    execution_time,
                },
            }),
        }
    }

    pub async fn fail_container(&self, container_id: String, error: String) -> Result<(), StateError> {
        let current_state = self.get_current_state().await;
        match current_state {
            ContainerState::Initial |
            ContainerState::Stopped { .. } |
            ContainerState::Failed { .. } => {
                Err(StateError::InvalidTransition {
                    from: current_state,
                    to: ContainerState::Failed {
                        container_id,
                        error,
                        occurred_at: Instant::now(),
                    },
                })
            },
            _ => {
                self.transition_to(ContainerState::Failed {
                    container_id,
                    error,
                    occurred_at: Instant::now(),
                }).await
            }
        }
    }
} 