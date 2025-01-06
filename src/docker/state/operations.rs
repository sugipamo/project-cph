use std::time::Instant;
use crate::error::Result;
use super::ContainerState;
use crate::docker::error::state_err;

pub async fn fail_container(current_state: &ContainerState, container_id: String, error: String) -> Result<ContainerState> {
    match current_state {
        ContainerState::Initial |
        ContainerState::Stopped { .. } |
        ContainerState::Failed { .. } => {
            Err(state_err(format!(
                "無効な状態からの失敗遷移: {}",
                current_state
            )))
        },
        _ => {
            Ok(ContainerState::Failed {
                container_id,
                error,
                occurred_at: Instant::now(),
            })
        }
    }
}

pub async fn create_container(current_state: &ContainerState, container_id: String) -> Result<ContainerState> {
    match current_state {
        ContainerState::Initial => {
            Ok(ContainerState::Created {
                container_id,
                created_at: Instant::now(),
            })
        },
        _ => {
            Err(state_err(format!(
                "無効な状態からの作成遷移: {}",
                current_state
            )))
        }
    }
}

pub async fn start_container(current_state: &ContainerState) -> Result<ContainerState> {
    match current_state {
        ContainerState::Created { container_id, .. } => {
            Ok(ContainerState::Running {
                container_id: container_id.clone(),
                started_at: Instant::now(),
            })
        },
        _ => {
            Err(state_err(format!(
                "無効な状態からの開始遷移: {}",
                current_state
            )))
        }
    }
}

pub async fn stop_container(current_state: &ContainerState) -> Result<ContainerState> {
    match current_state {
        ContainerState::Running { container_id, .. } |
        ContainerState::Executing { container_id, .. } => {
            Ok(ContainerState::Stopped {
                container_id: container_id.clone(),
                stopped_at: Instant::now(),
            })
        },
        _ => {
            Err(state_err(format!(
                "無効な状態からの停止遷移: {}",
                current_state
            )))
        }
    }
} 