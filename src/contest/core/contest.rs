use crate::config::{Config, ConfigBuilder};
use serde_json;
use super::{ContestState, state_manager::StateManager};
use crate::contest::error::Result;
use crate::fs::SafeFileSystem;

/// コンテスト情報を管理する構造体
#[derive(Debug)]
pub struct Contest {
    /// コンテストの状態
    state: ContestState,
    /// 設定情報
    config: Config,
    /// バァイルシステム操作
    fs: SafeFileSystem,
}

impl StateManager for Contest {
    fn state(&self) -> &ContestState {
        &self.state
    }

    fn state_mut(&mut self) -> &mut ContestState {
        &mut self.state
    }
}

impl Contest {
    /// サイト認証用のコンテストインスタンスを作成
    pub fn for_site_auth(config: Config) -> Result<Self> {
        Ok(Self {
            state: ContestState::new(),
            config,
            fs: SafeFileSystem::new()?,
        })
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

        Ok(Self {
            state,
            config,
            fs: SafeFileSystem::new()?.with_base_path(&active_dir),
        })
    }

    /// 設定を取得
    pub fn config(&self) -> &Config {
        &self.config
    }

    /// ファイルシステム操作を取得
    pub fn fs(&self) -> &SafeFileSystem {
        &self.fs
    }

    /// ファイルシステム操作を可変で取得
    pub fn fs_mut(&mut self) -> &mut SafeFileSystem {
        &mut self.fs
    }
}
