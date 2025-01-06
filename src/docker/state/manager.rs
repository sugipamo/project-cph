use std::sync::Arc;
use tokio::sync::RwLock;
use crate::error::Result;
use super::ContainerState;
use crate::docker::error::state_err;
use crate::docker::state::operations;

#[derive(Debug, Clone)]
pub struct ContainerStateManager {
    state: Arc<RwLock<ContainerState>>,
}

impl ContainerStateManager {
    pub fn new() -> Self {
        Self {
            state: Arc::new(RwLock::new(ContainerState::Initial)),
        }
    }

    pub async fn get_current_state(&self) -> ContainerState {
        self.state.read().await.clone()
    }

    pub async fn create_container(&self, container_id: String) -> Result<()> {
        let current_state = self.get_current_state().await;
        let new_state = operations::create_container(&current_state, container_id).await?;
        *self.state.write().await = new_state;
        Ok(())
    }

    pub async fn start_container(&self) -> Result<()> {
        let current_state = self.get_current_state().await;
        let new_state = operations::start_container(&current_state).await?;
        *self.state.write().await = new_state;
        Ok(())
    }

    pub async fn stop_container(&self) -> Result<()> {
        let current_state = self.get_current_state().await;
        let new_state = operations::stop_container(&current_state).await?;
        *self.state.write().await = new_state;
        Ok(())
    }

    pub async fn fail_container(&self, container_id: String, error: String) -> Result<()> {
        let current_state = self.get_current_state().await;
        let new_state = operations::fail_container(&current_state, container_id, error).await?;
        *self.state.write().await = new_state;
        Ok(())
    }

    pub async fn get_container_id(&self) -> Result<String> {
        let state = self.get_current_state().await;
        state.container_id()
            .map(String::from)
            .ok_or_else(|| state_err("コンテナIDが見つかりません".to_string()))
    }
} 