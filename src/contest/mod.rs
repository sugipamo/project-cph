pub mod error;
pub mod fs;

use crate::config::Config;
use error::{Result, ContestError};
use std::sync::Arc;
use std::path::{Path, PathBuf};

/// コンテスト管理を行う構造体
#[derive(Debug)]
pub struct Contest {
    config: Arc<Config>,
    site: Option<String>,
    contest_id: Option<String>,
    active_contest_dir: PathBuf,
}

impl Contest {
    /// 新しいコンテストインスタンスを作成
    pub fn new(config: Arc<Config>, contest_id: impl Into<String>) -> Result<Self> {
        let contest_id = contest_id.into();
        let active_contest_dir = PathBuf::from("active_contest");

        Ok(Self {
            config,
            site: None,
            contest_id: Some(contest_id),
            active_contest_dir,
        })
    }

    /// サイト認証用のインスタンスを作成
    pub fn for_site_auth(config: Arc<Config>) -> Result<Self> {
        Ok(Self {
            config,
            site: None,
            contest_id: None,
            active_contest_dir: PathBuf::from("active_contest"),
        })
    }

    /// サイトを設定
    pub fn set_site(&mut self, site: impl Into<String>) -> Result<()> {
        self.site = Some(site.into());
        Ok(())
    }

    /// コンテストを設定
    pub fn set_contest(&mut self, contest_id: impl Into<String>) {
        self.contest_id = Some(contest_id.into());
    }

    /// 設定を取得
    pub fn config(&self) -> &Arc<Config> {
        &self.config
    }

    /// サイトを取得
    pub fn site(&self) -> Option<&str> {
        self.site.as_deref()
    }

    /// コンテストIDを取得
    pub fn contest_id(&self) -> Option<&str> {
        self.contest_id.as_deref()
    }

    /// アクティブコンテストディレクトリを取得
    pub fn active_contest_dir(&self) -> &Path {
        &self.active_contest_dir
    }

    /// 問題のURLを取得
    pub fn get_problem_url(&self, problem_id: &str) -> Result<String> {
        let site = self.site.as_ref().ok_or_else(|| ContestError::Config {
            message: "サイトが設定されていません".to_string(),
            source: None,
        })?;

        let url_template = self.config.get::<String>(&format!("sites.{}.problem_url", site))?;
        let contest_id = self.contest_id.as_ref().ok_or_else(|| ContestError::Config {
            message: "コンテストIDが設定されていません".to_string(),
            source: None,
        })?;

        Ok(url_template
            .replace("{contest_id}", contest_id)
            .replace("{problem_id}", problem_id))
    }

    /// 問題のソリューションパスを取得
    pub fn get_solution_path(&self, problem_id: &str) -> Result<PathBuf> {
        let contest_id = self.contest_id.as_ref().ok_or_else(|| ContestError::Config {
            message: "コンテストIDが設定されていません".to_string(),
            source: None,
        })?;

        Ok(self.active_contest_dir
            .join(contest_id)
            .join(problem_id)
            .join("main.rs"))
    }

    /// 問題のディレクトリを作成
    pub fn create_problem_directory(&self, problem_id: &str) -> Result<()> {
        let contest_id = self.contest_id.as_ref().ok_or_else(|| ContestError::Config {
            message: "コンテストIDが設定されていません".to_string(),
            source: None,
        })?;

        let problem_dir = self.active_contest_dir.join(contest_id).join(problem_id);
        std::fs::create_dir_all(&problem_dir).map_err(|e| ContestError::FileSystem {
            message: "問題ディレクトリの作成に失敗".to_string(),
            source: e,
            path: problem_dir,
        })?;

        Ok(())
    }

    /// 設定を保存
    pub fn save(&self) -> Result<()> {
        // 設定の保存処理を実装
        Ok(())
    }
} 