use crate::docker::state::types::{ContainerState, StateError};

pub async fn validate_transition(current: &ContainerState, new: &ContainerState) -> Result<(), StateError> {
    match (current, new) {
        // 初期状態からの遷移
        (ContainerState::Initial, ContainerState::Created { .. }) => Ok(()),
        
        // Created状態からの遷移
        (ContainerState::Created { .. }, ContainerState::Running { .. }) |
        (ContainerState::Created { .. }, ContainerState::Failed { .. }) => {
            validate_container_id(current, new)
        }
        
        // Running状態からの遷移
        (ContainerState::Running { .. }, ContainerState::Executing { .. }) |
        (ContainerState::Running { .. }, ContainerState::Stopped { .. }) |
        (ContainerState::Running { .. }, ContainerState::Failed { .. }) => {
            validate_container_id(current, new)
        }
        
        // Executing状態からの遷移
        (ContainerState::Executing { .. }, ContainerState::Running { .. }) |
        (ContainerState::Executing { .. }, ContainerState::Stopped { .. }) |
        (ContainerState::Executing { .. }, ContainerState::Failed { .. }) => {
            validate_container_id(current, new)
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

pub fn validate_container_id(current: &ContainerState, new: &ContainerState) -> Result<(), StateError> {
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