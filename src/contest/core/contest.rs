use crate::config::Config;
use crate::contest::state::ContestState;
use crate::contest::state::manager::ContestStateManager;
use crate::contest::error::Result;
use crate::fs::FileManager;

/// コンテスト情報を管理する構造体
#[derive(Debug)]
pub struct Contest {
    /// 状態管理
    state_manager: ContestStateManager,
    /// 設定情報
    config: Config,
    /// バァイルシステム操作
    fs: FileManager,
}

impl Contest {
    /// サイト認証用のコンテストインスタンスを作成
    pub fn for_site_auth(config: Config) -> Result<Self> {
        Ok(Self {
            state_manager: ContestStateManager::new(ContestState::new()),
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
            state_manager: ContestStateManager::new(state),
            config,
            fs: FileManager::new()?.with_base_path(&active_dir),
        })
    }

    /// 状態を取得
    pub fn state(&self) -> &ContestState {
        self.state_manager.state()
    }

    /// 状態を可変で取得
    pub fn state_mut(&mut self) -> &mut ContestState {
        self.state_manager.state_mut()
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
}
