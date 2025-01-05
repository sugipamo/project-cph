use super::ContestState;

/// コンテストの状態を管理する構造体
#[derive(Debug)]
pub struct ContestStateManager {
    /// コンテストの状態
    state: ContestState,
}

impl ContestStateManager {
    /// 新しい状態管理インスタンスを作成
    pub fn new(state: ContestState) -> Self {
        Self { state }
    }

    /// 状態を取得
    pub fn state(&self) -> &ContestState {
        &self.state
    }

    /// 状態を可変で取得
    pub fn state_mut(&mut self) -> &mut ContestState {
        &mut self.state
    }
} 