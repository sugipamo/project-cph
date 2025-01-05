pub mod manager;

use std::path::PathBuf;
use serde::{Serialize, Deserialize};

/// コンテストの状態を表す構造体
#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct ContestState {
    /// アクティブなコンテストのディレクトリ
    #[serde(default)]
    pub active_contest_dir: PathBuf,

    /// コンテスト情報
    #[serde(default)]
    pub contest: String,

    /// 問題ID
    pub problem_id: Option<String>,

    /// 使用言語
    pub language: Option<String>,

    /// サイトID（例: atcoder, codeforces）
    #[serde(default)]
    pub site: String,
}

impl ContestState {
    /// 新しい状態を作成
    pub fn new() -> Self {
        Self::default()
    }

    /// 問題IDを設定
    pub fn with_problem(mut self, problem_id: &str) -> Self {
        self.problem_id = Some(problem_id.to_string());
        self
    }

    /// 言語を設定
    pub fn with_language(mut self, language: &str) -> Self {
        self.language = Some(language.to_string());
        self
    }

    /// コンテスト情報を設定
    pub fn with_contest(mut self, contest_id: &str) -> Self {
        self.contest = contest_id.to_string();
        self
    }

    /// サイトIDを設定
    pub fn with_site(mut self, site: &str) -> Self {
        self.site = site.to_string();
        self
    }

    /// アクティブディレクトリを設定
    pub fn with_active_dir(mut self, dir: PathBuf) -> Self {
        self.active_contest_dir = dir;
        self
    }

    /// 問題IDを取得
    pub fn problem_id(&self) -> Option<&str> {
        self.problem_id.as_deref()
    }

    /// 言語を取得
    pub fn language(&self) -> Option<&str> {
        self.language.as_deref()
    }

    /// アクティブディレクトリを取得
    pub fn active_dir(&self) -> &PathBuf {
        &self.active_contest_dir
    }

    /// 問題IDを設定（可変参照版）
    pub fn set_problem(&mut self, problem_id: &str) {
        self.problem_id = Some(problem_id.to_string());
    }
} 