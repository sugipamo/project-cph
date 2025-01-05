use serde::{Serialize, Deserialize};
use std::path::PathBuf;

/// コンテストの状態を管理する構造体
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContestState {
    /// アクティブなコンテストのディレクトリ
    #[serde(default)]
    active_contest_dir: PathBuf,

    /// コンテスト情報
    contest: String,

    /// 問題ID
    problem: Option<String>,

    /// 使用言語
    language: Option<String>,

    /// サイトID（例: atcoder, codeforces）
    site: String,
}

impl Default for ContestState {
    fn default() -> Self {
        Self::new()
    }
}

impl ContestState {
    /// 新しい状態を作成
    pub fn new() -> Self {
        Self {
            active_contest_dir: PathBuf::new(),
            contest: String::new(),
            problem: None,
            language: None,
            site: String::new(),
        }
    }

    /// 問題IDを設定
    pub fn with_problem(mut self, problem_id: &str) -> Self {
        self.set_problem(problem_id);
        self
    }

    /// 言語を設定
    pub fn with_language(mut self, language: &str) -> Self {
        self.set_language(language);
        self
    }

    /// コンテストIDを設定
    pub fn with_contest(mut self, contest_id: &str) -> Self {
        self.set_contest(contest_id);
        self
    }

    /// サイトを設定
    pub fn with_site(mut self, site: &str) -> Self {
        self.set_site(site);
        self
    }

    /// アクティブディレクトリを設定
    pub fn with_active_dir(mut self, dir: PathBuf) -> Self {
        self.set_active_dir(dir);
        self
    }

    /// 問題IDを取得
    pub fn problem_id(&self) -> Option<&str> {
        self.problem.as_deref()
    }

    /// 言語を取得
    pub fn language(&self) -> Option<&str> {
        self.language.as_deref()
    }

    /// コンテストIDを取得
    pub fn contest_id(&self) -> &str {
        &self.contest
    }

    /// サイトを取得
    pub fn site(&self) -> &str {
        &self.site
    }

    /// アクティブディレクトリを取得
    pub fn active_dir(&self) -> &PathBuf {
        &self.active_contest_dir
    }

    /// 問題を設定
    pub fn set_problem(&mut self, problem_id: &str) {
        self.problem = Some(problem_id.to_string());
    }

    /// 言語を設定
    pub fn set_language(&mut self, language: &str) {
        self.language = Some(language.to_string());
    }

    /// コンテストIDを設定
    pub fn set_contest(&mut self, contest_id: &str) {
        self.contest = contest_id.to_string();
    }

    /// サイトを設定
    pub fn set_site(&mut self, site: &str) {
        self.site = site.to_string();
    }

    /// アクティブディレクトリを設定
    pub fn set_active_dir(&mut self, dir: PathBuf) {
        self.active_contest_dir = dir;
    }

    /// 状態が有効かどうかを確認
    pub fn is_valid(&self) -> bool {
        !self.contest.is_empty() && !self.site.is_empty() && !self.active_contest_dir.as_os_str().is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_contest_state_builder() {
        let state = ContestState::new()
            .with_problem("abc123")
            .with_language("rust")
            .with_contest("abc")
            .with_site("atcoder")
            .with_active_dir(PathBuf::from("/tmp/contest"));

        assert_eq!(state.problem_id(), Some("abc123"));
        assert_eq!(state.language(), Some("rust"));
        assert_eq!(state.contest_id(), "abc");
        assert_eq!(state.site(), "atcoder");
        assert_eq!(state.active_dir(), &PathBuf::from("/tmp/contest"));
        assert!(state.is_valid());
    }

    #[test]
    fn test_contest_state_setters() {
        let mut state = ContestState::new();
        state.set_problem("abc123");
        state.set_language("rust");
        state.set_contest("abc");
        state.set_site("atcoder");
        state.set_active_dir(PathBuf::from("/tmp/contest"));

        assert_eq!(state.problem_id(), Some("abc123"));
        assert_eq!(state.language(), Some("rust"));
        assert_eq!(state.contest_id(), "abc");
        assert_eq!(state.site(), "atcoder");
        assert_eq!(state.active_dir(), &PathBuf::from("/tmp/contest"));
        assert!(state.is_valid());
    }

    #[test]
    fn test_invalid_state() {
        let state = ContestState::new();
        assert!(!state.is_valid());
    }
}
