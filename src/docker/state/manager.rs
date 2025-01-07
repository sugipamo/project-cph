use std::sync::Arc;
use tokio::sync::RwLock;
use crate::error::Result;
use super::ContainerState;
use crate::docker::error::state_err;
use super::types::{StateInfo, StateType};

#[derive(Debug, Clone)]
pub struct ContainerStateManager {
    state: Arc<RwLock<ContainerState>>,
}

impl ContainerStateManager {
    pub fn new() -> Self {
        Self {
            state: Arc::new(RwLock::new(ContainerState::new())),
        }
    }

    pub async fn get_current_state(&self) -> ContainerState {
        self.state.read().await.clone()
    }

    pub async fn create_container(&self, container_id: String) -> Result<()> {
        let current_state = self.get_current_state().await;
        if !matches!(current_state, ContainerState::Initial) {
            return Err(state_err(
                "状態遷移",
                format!("無効な状態からの作成遷移: {}", current_state)
            ));
        }
        *self.state.write().await = ContainerState::create(container_id);
        Ok(())
    }

    pub async fn start_container(&self) -> Result<()> {
        let current_state = self.get_current_state().await;
        let new_state = current_state.start()
            .ok_or_else(|| state_err(
                "状態遷移",
                format!("無効な状態からの開始遷移: {}", current_state)
            ))?;
        *self.state.write().await = new_state;
        Ok(())
    }

    pub async fn execute_command(&self, command: String) -> Result<()> {
        let current_state = self.get_current_state().await;
        let new_state = current_state.execute(command)
            .ok_or_else(|| state_err(
                "状態遷移",
                format!("無効な状態からのコマンド実行遷移: {}", current_state)
            ))?;
        *self.state.write().await = new_state;
        Ok(())
    }

    pub async fn stop_container(&self) -> Result<()> {
        let current_state = self.get_current_state().await;
        let new_state = current_state.stop()
            .ok_or_else(|| state_err(
                "状態遷移",
                format!("無効な状態からの停止遷移: {}", current_state)
            ))?;
        *self.state.write().await = new_state;
        Ok(())
    }

    pub async fn fail_container(&self, error: String) -> Result<()> {
        let current_state = self.get_current_state().await;
        let new_state = current_state.fail(error)
            .ok_or_else(|| state_err(
                "状態遷移",
                format!("無効な状態からの失敗遷移: {}", current_state)
            ))?;
        *self.state.write().await = new_state;
        Ok(())
    }

    pub async fn get_container_id(&self) -> Result<String> {
        let state = self.get_current_state().await;
        state.container_id()
            .map(String::from)
            .ok_or_else(|| state_err("状態管理", "コンテナIDが見つかりません"))
    }

    pub async fn regenerate_container(&self) -> Result<()> {
        let current_state = self.get_current_state().await;
        let new_state = current_state.regenerate()
            .ok_or_else(|| state_err(
                "状態遷移",
                format!("無効な状態からの再生成遷移: {}", current_state)
            ))?;
        *self.state.write().await = new_state;
        Ok(())
    }

    pub async fn restore_state(&self, state_info: StateInfo) -> Result<()> {
        let current_state = self.get_current_state().await;
        if !matches!(current_state, ContainerState::Created { .. }) {
            return Err(state_err(
                "状態遷移",
                format!("無効な状態からの状態復元: {}", current_state)
            ));
        }

        let new_state = match state_info.state_type {
            StateType::Running => ContainerState::Running {
                container_id: state_info.container_id,
                started_at: state_info.timestamp,
            },
            StateType::Executing(command) => ContainerState::Executing {
                container_id: state_info.container_id,
                started_at: state_info.timestamp,
                command,
            },
            StateType::Stopped => ContainerState::Stopped {
                container_id: state_info.container_id,
                stopped_at: state_info.timestamp,
                exit_status: None,
            },
            StateType::Failed(error) => ContainerState::Failed {
                container_id: state_info.container_id,
                error,
                occurred_at: state_info.timestamp,
            },
        };

        *self.state.write().await = new_state;
        Ok(())
    }
} 