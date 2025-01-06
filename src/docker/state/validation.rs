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
            Err(docker_err(format!(
                "コンテナIDが一致しません。\n現在のID: {}\n新しいID: {}\nコンテナIDは状態遷移中に変更できません。",
                current_id, new_id
            )))
        }
        _ => Ok(())
    }
}

#[allow(dead_code)]
fn validate_state_transition(current: &ContainerState, new: &ContainerState) -> Result<()> {
    use ContainerState::*;
    
    match (current, new) {
        // 初期状態からの遷移
        (Initial, Created { .. }) => Ok(()),
        
        // Created状態からの遷移
        (Created { .. }, Running { .. }) |
        (Created { .. }, Failed { .. }) => Ok(()),
        
        // Running状態からの遷移
        (Running { .. }, Executing { .. }) |
        (Running { .. }, Stopped { .. }) |
        (Running { .. }, Failed { .. }) => Ok(()),
        
        // Executing状態からの遷移
        (Executing { .. }, Running { .. }) |
        (Executing { .. }, Stopped { .. }) |
        (Executing { .. }, Failed { .. }) => Ok(()),
        
        // 終端状態からの遷移は許可しない
        (Stopped { .. }, _) => {
            Err(docker_err(format!(
                "停止済みのコンテナの状態を変更することはできません。\n現在の状態: {}\n要求された状態: {}\n新しい操作を開始するには、新しいコンテナを作成してください。",
                current, new
            )))
        }
        (Failed { .. }, _) => {
            Err(docker_err(format!(
                "失敗状態のコンテナの状態を変更することはできません。\n現在の状態: {}\n要求された状態: {}\nエラーを解決し、新しいコンテナで再試行してください。",
                current, new
            )))
        }
        
        // その他の遷移は無効
        _ => Err(docker_err(format!(
            "無効な状態遷移が要求されました。\n現在の状態: {}\n要求された状態: {}\n許可される遷移については、ドキュメントを参照してください。",
            current, new
        ))),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_valid_transitions() {
        let initial = ContainerState::Initial;
        let created = ContainerState::Created {
            container_id: Some("test_id".to_string())
        };
        let running = ContainerState::Running {
            container_id: Some("test_id".to_string())
        };

        // 初期状態 -> Created
        assert!(validate_transition(&initial, &created).await.is_ok());

        // Created -> Running
        assert!(validate_transition(&created, &running).await.is_ok());
    }

    #[tokio::test]
    async fn test_invalid_container_id_transition() {
        let current = ContainerState::Running {
            container_id: Some("id1".to_string())
        };
        let new = ContainerState::Running {
            container_id: Some("id2".to_string())
        };

        let result = validate_transition(&current, &new).await;
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("コンテナIDが一致しません"));
    }

    #[tokio::test]
    async fn test_invalid_state_transitions() {
        let stopped = ContainerState::Stopped {
            container_id: Some("test_id".to_string()),
            exit_code: 0
        };
        let running = ContainerState::Running {
            container_id: Some("test_id".to_string())
        };

        // 停止状態からの遷移は許可されない
        let result = validate_transition(&stopped, &running).await;
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("停止済みのコンテナ"));
    }
} 