use std::sync::Arc;
use tokio::sync::RwLock;
use anyhow::Result;

use super::container_state::Info;

/// Dockerコンテナの状態を管理する構造体
///
/// # Fields
/// * `state` - コンテナの状態情報
#[derive(Debug, Default)]
pub struct Manager {
    state: Arc<RwLock<Option<Info>>>,
}

impl Manager {
    /// 新しい状態管理インスタンスを作成します
    ///
    /// # Returns
    /// * `Self` - 新しい状態管理インスタンス
    #[must_use = "この関数は新しい状態管理インスタンスを返します"]
    pub fn new() -> Self {
        Self {
            state: Arc::new(RwLock::new(None)),
        }
    }

    /// 現在のコンテナの状態を取得します
    ///
    /// # Returns
    /// * `Option<Info>` - コンテナの状態情報（存在する場合）
    pub async fn get_state(&self) -> Option<Info> {
        self.state.read().await.clone()
    }

    /// コンテナの状態を設定します
    ///
    /// # Arguments
    /// * `state` - 設定する状態
    ///
    /// # Returns
    /// * `Result<()>` - 設定結果
    ///
    /// # Errors
    /// * 状態の設定に失敗した場合（ロックの取得に失敗など）
    pub async fn set_state(&self, state: Info) -> Result<()> {
        *self.state.write().await = Some(state);
        Ok(())
    }

    /// コンテナの状態をクリアします
    ///
    /// # Returns
    /// * `Result<()>` - クリア結果
    ///
    /// # Errors
    /// * 状態のクリアに失敗した場合（ロックの取得に失敗など）
    pub async fn clear_state(&self) -> Result<()> {
        *self.state.write().await = None;
        Ok(())
    }
} 