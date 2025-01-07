use std::time::Instant;
use std::sync::Arc;
use crate::error::Result;
use super::ContainerState;
use crate::docker::error::state_err;

pub trait StateOperations {
    fn fail(&mut self, current_state: &ContainerState) -> Result<()>;
    fn create(&mut self, current_state: &ContainerState) -> Result<()>;
    fn start(&mut self, current_state: &ContainerState) -> Result<()>;
    fn stop(&mut self, current_state: &ContainerState) -> Result<()>;
}

pub async fn fail_container(current_state: &ContainerState, container_id: String, error: String) -> Result<ContainerState> {
    match current_state {
        ContainerState::Initial |
        ContainerState::Stopped { .. } |
        ContainerState::Failed { .. } => {
            Err(state_err(
                "状態遷移",
                format!("無効な状態からの失敗遷移: {}", current_state)
            ))
        },
        _ => {
            Ok(ContainerState::Failed {
                container_id: Arc::new(container_id),
                error: Arc::new(error),
                occurred_at: Arc::new(Instant::now()),
            })
        }
    }
}

pub async fn create_container(current_state: &ContainerState, container_id: String) -> Result<ContainerState> {
    match current_state {
        ContainerState::Initial => {
            Ok(ContainerState::Created {
                container_id: Arc::new(container_id),
                created_at: Arc::new(Instant::now()),
            })
        },
        _ => {
            Err(state_err(
                "状態遷移",
                format!("無効な状態からの作成遷移: {}", current_state)
            ))
        }
    }
}

pub async fn start_container(current_state: &ContainerState) -> Result<ContainerState> {
    match current_state {
        ContainerState::Created { container_id, .. } => {
            Ok(ContainerState::Running {
                container_id: Arc::clone(container_id),
                started_at: Arc::new(Instant::now()),
            })
        },
        _ => {
            Err(state_err(
                "状態遷移",
                format!("無効な状態からの開始遷移: {}", current_state)
            ))
        }
    }
}

pub async fn stop_container(current_state: &ContainerState) -> Result<ContainerState> {
    match current_state {
        ContainerState::Running { container_id, .. } |
        ContainerState::Executing { container_id, .. } => {
            Ok(ContainerState::Stopped {
                container_id: Arc::clone(container_id),
                stopped_at: Arc::new(Instant::now()),
                exit_status: None,
            })
        },
        _ => {
            Err(state_err(
                "状態遷移",
                format!("無効な状態からの停止遷移: {}", current_state)
            ))
        }
    }
} 