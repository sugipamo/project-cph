use crate::config::Config;
use crate::contest::model::ContestState;
use crate::contest::error::Result;
use crate::fs::FileManager;

/// コンテスト情報を管理する構造体
#[derive(Debug)]
pub struct Contest {
    /// 状態
    state: ContestState,
    /// 設定情報
    config: Config,
    /// ファイルシステム操作
    fs: FileManager,
}

impl Contest {
    /// サイト認証用のコンテストインスタンスを作成
    pub fn for_site_auth(config: Config) -> Result<Self> {
        Ok(Self {
            state: ContestState::new(),
            config,
            fs: FileManager::new()?,
        })
    }

    /// 新しいコンテストインスタンスを作成
    pub fn new(config: Config, problem_id: &str) -> Result<Self> {
        let active_dir = config.get::<String>("system.contest_dir.active")?;
        let mut state = ContestState::new()
            .with_problem(problem_id)
            .with_active_dir(active_dir.clone().into());

        if let Ok(default_lang) = config.get::<String>("languages.default") {
            state = state.with_language(&default_lang);
        }

        Ok(Self {
            state,
            config,
            fs: FileManager::new()?.with_base_path(&active_dir),
        })
    }

    /// 状態を取得
    pub fn state(&self) -> &ContestState {
        &self.state
    }

    /// 状態を可変で取得
    pub fn state_mut(&mut self) -> &mut ContestState {
        &mut self.state
    }

    /// 設定を取得
    pub fn config(&self) -> &Config {
        &self.config
    }

    /// ファイルシステム操作を取得
    pub fn fs(&self) -> &FileManager {
        &self.fs
    }

    /// ファイルシステム操作を可変で取得
    pub fn fs_mut(&mut self) -> &mut FileManager {
        &mut self.fs
    }

    /// 状態を更新
    pub fn update_state<F>(&mut self, f: F) -> Result<()>
    where
        F: FnOnce(&mut ContestState) -> Result<()>,
    {
        self.state.update(f)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    fn create_test_config() -> Config {
        let mut config_map = HashMap::new();
        config_map.insert("system.contest_dir.active".to_string(), "/tmp/contest".to_string());
        config_map.insert("languages.default".to_string(), "rust".to_string());
        Config::from_str(&serde_json::to_string(&config_map).unwrap(), Config::builder()).unwrap()
    }

    #[test]
    fn test_contest_creation() -> Result<()> {
        let config = create_test_config();
        let contest = Contest::new(config.clone(), "abc123")?;
        
        assert_eq!(contest.state().problem_id(), Some("abc123"));
        assert_eq!(contest.state().language(), Some("rust"));
        assert_eq!(contest.state().active_dir(), &std::path::PathBuf::from("/tmp/contest"));
        Ok(())
    }

    #[test]
    fn test_state_update() -> Result<()> {
        let config = create_test_config();
        let mut contest = Contest::for_site_auth(config)?;
        
        contest.update_state(|state| {
            state.set_problem("abc123");
            state.set_language("rust");
            Ok(())
        })?;

        assert_eq!(contest.state().problem_id(), Some("abc123"));
        assert_eq!(contest.state().language(), Some("rust"));
        Ok(())
    }
} 