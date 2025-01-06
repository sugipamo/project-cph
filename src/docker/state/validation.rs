use crate::error::Result;
use super::types::ContainerState;
use crate::docker::error::docker_err;

#[allow(dead_code)]
pub async fn validate_transition(current: &ContainerState, new: &ContainerState) -> Result<()> {
    validate_container_id(current, new)?;
    validate_state_transition(current, new)?;
    Ok(())
}

#[allow(dead_code)]
fn validate_container_id(current: &ContainerState, new: &ContainerState) -> Result<()> {
    match (current.container_id(), new.container_id()) {
        (Some(current_id), Some(new_id)) if current_id != new_id => {
            Err(docker_err("コンテナIDが一致しません".to_string()))
        }
        _ => Ok(())
    }
}

#[allow(dead_code)]
fn validate_state_transition(current: &ContainerState, new: &ContainerState) -> Result<()> {
    match (current, new) {
        // 初期状態からの遷移
        (ContainerState::Initial, ContainerState::Created { .. }) => Ok(()),
        
        // Created状態からの遷移
        (ContainerState::Created { .. }, ContainerState::Running { .. }) |
        (ContainerState::Created { .. }, ContainerState::Failed { .. }) => Ok(()),
        
        // Running状態からの遷移
        (ContainerState::Running { .. }, ContainerState::Executing { .. }) |
        (ContainerState::Running { .. }, ContainerState::Stopped { .. }) |
        (ContainerState::Running { .. }, ContainerState::Failed { .. }) => Ok(()),
        
        // Executing状態からの遷移
        (ContainerState::Executing { .. }, ContainerState::Running { .. }) |
        (ContainerState::Executing { .. }, ContainerState::Stopped { .. }) |
        (ContainerState::Executing { .. }, ContainerState::Failed { .. }) => Ok(()),
        
        // 終端状態からの遷移は許可しない
        (ContainerState::Stopped { .. }, _) |
        (ContainerState::Failed { .. }, _) => {
            Err(docker_err(format!(
                "無効な状態遷移: {} -> {}",
                current, new
            )))
        }
        
        // その他の遷移は無効
        _ => Err(docker_err(format!(
            "無効な状態遷移: {} -> {}",
            current, new
        ))),
    }
} 