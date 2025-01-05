use crate::contest::error::Result;
use super::ContestState;

/// コンテストの状態管理を行うトレイト
pub trait StateManager {
    /// 現在の状態を取得
    fn state(&self) -> &ContestState;
    
    /// 可変の状態を取得
    fn state_mut(&mut self) -> &mut ContestState;
    
    /// 状態を更新
    fn update_state<F>(&mut self, f: F) -> Result<()>
    where
        F: FnOnce(&mut ContestState) -> Result<()>;
}
