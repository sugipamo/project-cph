use crate::config::Config;
use super::ContestState;
use crate::contest::error::{Result, ContestError};
use crate::contest::fs::FileManager;
use std::sync::Arc;

/// コンテスト情報を管理する構造体
#[derive(Debug)]
pub struct Contest {
    /// コンテストの状態
    state: ContestState,
    /// 設定情報
    config: Arc<Config>,
    /// ファイル操作マネージャー
    fs_manager: Arc<FileManager>,
}

impl Contest {
    /// サイト認証用のコンテストインスタンスを作成
    pub fn for_site_auth(config: Arc<Config>) -> Result<Self> {
        Ok(Self {
            state: ContestState::new(),
            config,
            fs_manager: Arc::new(FileManager::new()?),
        })
    }

    /// 新しいコンテストインスタンスを作成
    pub fn new(config: Arc<Config>, problem_id: &str) -> Result<Self> {
        let active_dir = config.get::<String>("system.contest_dir.active")
            .map_err(|e| ContestError::Config {
                message: format!("アクティブディレクトリの設定取得に失敗: {}", e),
                source: None,
            })?;

        let mut state = ContestState::new()
            .with_problem(problem_id)
            .with_active_dir(active_dir.into());

        // デフォルト言語を設定
        if let Ok(default_lang) = config.get::<String>("languages.default") {
            state = state.with_language(&default_lang);
        }

        Ok(Self {
            state,
            config,
            fs_manager: Arc::new(FileManager::new()?),
        })
    }

    /// コンテストの状態を取得
    pub fn state(&self) -> &ContestState {
        &self.state
    }

    /// コンテストの状態を可変で取得
    pub fn state_mut(&mut self) -> &mut ContestState {
        &mut self.state
    }

    /// 設定を取得
    pub fn config(&self) -> &Config {
        &self.config
    }

    /// ファイルマネージャーを取得
    pub fn fs_manager(&self) -> &FileManager {
        &self.fs_manager
    }
} 