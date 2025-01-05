use crate::contest::error::{Result, Error};
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

    /// 状態が有効かどうかを確認
    fn validate_state(&self) -> Result<()> {
        if !self.state().is_valid() {
            return Err(Error::InvalidState("必須フィールドが設定されていません".into()));
        }
        Ok(())
    }

    /// 問題IDを設定
    fn set_problem(&mut self, problem_id: &str) -> Result<()> {
        self.update_state(|state| {
            state.set_problem(problem_id);
            Ok(())
        })
    }

    /// 言語を設定
    fn set_language(&mut self, language: &str) -> Result<()> {
        self.update_state(|state| {
            state.set_language(language);
            Ok(())
        })
    }

    /// コンテストIDを設定
    fn set_contest(&mut self, contest_id: &str) -> Result<()> {
        self.update_state(|state| {
            state.set_contest(contest_id);
            Ok(())
        })
    }

    /// サイトを設定
    fn set_site(&mut self, site: &str) -> Result<()> {
        self.update_state(|state| {
            state.set_site(site);
            Ok(())
        })
    }

    /// アクティブディレクトリを設定
    fn set_active_dir(&mut self, dir: std::path::PathBuf) -> Result<()> {
        self.update_state(|state| {
            state.set_active_dir(dir);
            Ok(())
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    struct TestManager {
        state: ContestState,
    }

    impl StateManager for TestManager {
        fn state(&self) -> &ContestState {
            &self.state
        }

        fn state_mut(&mut self) -> &mut ContestState {
            &mut self.state
        }

        fn update_state<F>(&mut self, f: F) -> Result<()>
        where
            F: FnOnce(&mut ContestState) -> Result<()>,
        {
            f(&mut self.state)
        }
    }

    #[test]
    fn test_state_manager_operations() -> Result<()> {
        let mut manager = TestManager {
            state: ContestState::new(),
        };

        manager.set_problem("abc123")?;
        manager.set_language("rust")?;
        manager.set_contest("abc")?;
        manager.set_site("atcoder")?;
        manager.set_active_dir(PathBuf::from("/tmp/contest"))?;

        assert!(manager.validate_state().is_ok());
        Ok(())
    }

    #[test]
    fn test_invalid_state_validation() {
        let manager = TestManager {
            state: ContestState::new(),
        };

        assert!(manager.validate_state().is_err());
    }
}
