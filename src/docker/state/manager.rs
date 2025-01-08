use std::sync::Arc;
use tokio::sync::RwLock;
use anyhow::Result;

use super::container_state::Info;

#[derive(Debug, Default)]
pub struct Manager {
    state: Arc<RwLock<Option<Info>>>,
}

impl Manager {
    #[must_use]
    pub fn new() -> Self {
        Self {
            state: Arc::new(RwLock::new(None)),
        }
    }

    pub async fn get_state(&self) -> Option<Info> {
        self.state.read().await.clone()
    }

    /// コンテナの状態を設定します
    ///
    /// # Arguments
    /// * `state` - 設定する状態
    ///
    /// # Errors
    /// * 状態の設定に失敗した場合
    pub async fn set_state(&self, state: Info) -> Result<()> {
        *self.state.write().await = Some(state);
        Ok(())
    }

    /// コンテナの状態をクリアします
    ///
    /// # Errors
    /// * 状態のクリアに失敗した場合
    pub async fn clear_state(&self) -> Result<()> {
        *self.state.write().await = None;
        Ok(())
    }
} 