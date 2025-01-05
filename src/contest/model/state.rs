use std::path::PathBuf;
use serde::{Serialize, Deserialize};
use crate::contest::error::Result;

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

    /// 問題IDを設定
    pub fn set_problem(&mut self, problem_id: &str) {
        self.problem_id = Some(problem_id.to_string());
    }

    /// 言語を設定
    pub fn set_language(&mut self, language: &str) {
        self.language = Some(language.to_string());
    }

    /// コンテストIDを設定
    pub fn set_contest(&mut self, contest_id: &str) {
        self.contest = contest_id.to_string();
    }

    /// サイトIDを設定
    pub fn set_site(&mut self, site: &str) {
        self.site = site.to_string();
    }

    /// アクティブディレクトリを設定
    pub fn set_active_dir(&mut self, dir: PathBuf) {
        self.active_contest_dir = dir;
    }

    /// 状態を更新
    pub fn update<F>(&mut self, f: F) -> Result<()>
    where
        F: FnOnce(&mut Self) -> Result<()>,
    {
        f(self)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_contest_state_new() {
        let state = ContestState::new();
        assert!(state.problem_id.is_none());
        assert!(state.language.is_none());
        assert_eq!(state.contest, "");
        assert_eq!(state.site, "");
        assert_eq!(state.active_contest_dir, PathBuf::new());
    }

    #[test]
    fn test_contest_state_with_methods() {
        let state = ContestState::new()
            .with_problem("abc001_a")
            .with_language("rust")
            .with_contest("abc001")
            .with_site("atcoder")
            .with_active_dir(PathBuf::from("/tmp/contest"));

        assert_eq!(state.problem_id(), Some("abc001_a"));
        assert_eq!(state.language(), Some("rust"));
        assert_eq!(state.contest, "abc001");
        assert_eq!(state.site, "atcoder");
        assert_eq!(state.active_dir(), &PathBuf::from("/tmp/contest"));
    }

    #[test]
    fn test_contest_state_set_methods() {
        let mut state = ContestState::new();
        
        state.set_problem("abc001_a");
        state.set_language("rust");
        state.set_contest("abc001");
        state.set_site("atcoder");
        state.set_active_dir(PathBuf::from("/tmp/contest"));

        assert_eq!(state.problem_id(), Some("abc001_a"));
        assert_eq!(state.language(), Some("rust"));
        assert_eq!(state.contest, "abc001");
        assert_eq!(state.site, "atcoder");
        assert_eq!(state.active_dir(), &PathBuf::from("/tmp/contest"));
    }

    #[test]
    fn test_contest_state_update() {
        let mut state = ContestState::new();
        
        state.update(|s| {
            s.set_problem("abc001_a");
            s.set_language("rust");
            Ok(())
        }).unwrap();

        assert_eq!(state.problem_id(), Some("abc001_a"));
        assert_eq!(state.language(), Some("rust"));
    }
} 