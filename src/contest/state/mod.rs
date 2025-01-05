pub mod manager;

use std::path::PathBuf;

/// コンテストの状態を表す構造体
#[derive(Debug, Default)]
pub struct ContestState {
    /// 問題ID
    problem_id: Option<String>,
    /// 使用言語
    language: Option<String>,
    /// アクティブディレクトリ
    active_dir: Option<PathBuf>,
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

    /// アクティブディレクトリを設定
    pub fn with_active_dir(mut self, active_dir: PathBuf) -> Self {
        self.active_dir = Some(active_dir);
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
    pub fn active_dir(&self) -> Option<&PathBuf> {
        self.active_dir.as_ref()
    }
} 