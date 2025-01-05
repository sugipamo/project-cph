use crate::config::{Config, ConfigBuilder};
use serde_json;
use super::{ContestState, state_manager::StateManager};
use crate::contest::error::Result;
use crate::contest::fs::BackupManager;

/// コンテスト情報を管理する構造体
#[derive(Debug)]
pub struct Contest {
    /// コンテストの管理者
    manager: ContestManager,
}

/// コンテストの内部状態を管理する構造体
#[derive(Debug)]
struct ContestManager {
    /// コンテストの状態
    state: ContestState,
    /// 設定情報
    config: Config,
    /// バックアップマネージャー
    backup_manager: BackupManager,
}

impl StateManager for ContestManager {
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

impl ContestManager {
    /// 新しいコンテスト管理者を作成
    fn new(config: Config, state: ContestState) -> Result<Self> {
        Ok(Self {
            state,
            config,
            backup_manager: BackupManager::new()?,
        })
    }

    /// 設定を取得
    fn config(&self) -> &Config {
        &self.config
    }

    /// バックアップマネージャーを取得
    fn backup_manager(&self) -> &BackupManager {
        &self.backup_manager
    }

    /// バックアップマネージャーを可変で取得
    fn backup_manager_mut(&mut self) -> &mut BackupManager {
        &mut self.backup_manager
    }
}

impl Contest {
    /// サイト認証用のコンテストインスタンスを作成
    pub fn for_site_auth(config: Config) -> Result<Self> {
        let manager = ContestManager::new(config, ContestState::new())?;
        Ok(Self { manager })
    }

    /// 新しいコンテストインスタンスを作成
    pub fn new(config: Config, problem_id: &str) -> Result<Self> {
        let active_dir = config.get::<String>("system.contest_dir.active")?;
        let mut state = ContestState::new()
            .with_problem(problem_id)
            .with_active_dir(active_dir.into());

        if let Ok(default_lang) = config.get::<String>("languages.default") {
            state = state.with_language(&default_lang);
        }

        let manager = ContestManager::new(config, state)?;
        Ok(Self { manager })
    }

    /// 状態を取得
    pub fn state(&self) -> &ContestState {
        self.manager.state()
    }

    /// 状態を可変で取得
    pub fn state_mut(&mut self) -> &mut ContestState {
        self.manager.state_mut()
    }

    /// 設定を取得
    pub fn config(&self) -> &Config {
        self.manager.config()
    }

    /// バックアップマネージャーを取得
    pub fn backup_manager(&self) -> &BackupManager {
        self.manager.backup_manager()
    }

    /// バックアップマネージャーを可変で取得
    pub fn backup_manager_mut(&mut self) -> &mut BackupManager {
        self.manager.backup_manager_mut()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::Config;
    use std::collections::HashMap;

    #[test]
    fn test_contest_creation() -> Result<()> {
        let mut config_map = HashMap::new();
        config_map.insert("system.contest_dir.active".to_string(), "/tmp/contest".to_string());
        config_map.insert("languages.default".to_string(), "rust".to_string());
        let config = Config::from_str(&serde_json::to_string(&config_map)?, Config::builder())?;

        let contest = Contest::new(config.clone(), "abc123")?;
        
        assert_eq!(contest.state().problem_id(), Some("abc123"));
        assert_eq!(contest.state().language(), Some("rust"));
        assert_eq!(contest.state().active_dir(), "/tmp/contest");
        Ok(())
    }

    #[test]
    fn test_state_access() -> Result<()> {
        let config = Config::load()?;
        let mut contest = Contest::for_site_auth(config)?;
        
        contest.state_mut().set_problem("xyz987");
        assert_eq!(contest.state().problem_id(), Some("xyz987"));
        Ok(())
    }

    #[test]
    fn test_config_and_fs_manager_access() -> Result<()> {
        let config = Config::load()?;
        let contest = Contest::for_site_auth(config.clone())?;
        
        assert!(std::ptr::eq(contest.config(), &config));
        assert!(contest.backup_manager().is_ok());
        Ok(())
    }
}
