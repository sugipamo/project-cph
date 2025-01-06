use crate::docker::error::state_err;
use crate::error::Result;
use super::ContainerState;

pub async fn validate_transition(current: &ContainerState, new: &ContainerState) -> Result<()> {
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
            Err(state_err(format!(
                "無効な状態遷移: {} -> {}",
                current, new
            )))
        }
        
        // その他の遷移は無効
        _ => Err(state_err(format!(
            "無効な状態遷移: {} -> {}",
            current, new
        ))),
    }
}

fn validate_container_id(current: &ContainerState, new: &ContainerState) -> Result<()> {
    let current_id = current.container_id();
    let new_id = new.container_id();
    
    if current_id != new_id {
        Err(state_err(format!(
            "コンテナIDが一致しません: {} != {}",
            current_id.unwrap_or("なし"),
            new_id.unwrap_or("なし")
        )))
    } else {
        Ok(())
    }
} 