// ContestStateとValidatedStateの実装について：
// 
// 当初はCow<'static, str>やStringの使用を検討しましたが、以下の理由でArcを採用しています：
// 1. イミュータブルな設計の維持
//    - validate()メソッドで所有権の移動が不要（Arc::cloneで対応）
//    - 元のContestStateは変更されず再利用可能
// 
// 2. 将来のマルチスレッド対応
//    - Arcによりスレッド間で安全に共有可能
//    - 後からの変更コストを最小化
// 
// 3. パフォーマンスの最適化
//    - Arc::cloneは参照カウントの増加のみで、実データのコピーは発生しない
//    - メモリ効率が良い
//
// これらの理由から、シンプルさと将来の拡張性を両立する設計としてArcを採用しています。

use std::path::PathBuf;
use std::sync::Arc;
use crate::error::Result;
use crate::error::contest::ContestErrorKind;
use crate::contest::error::contest_error;

#[derive(Debug, Clone)]
pub struct ContestState {
    site: Option<Arc<String>>,
    contest_id: Option<Arc<String>>,
    problem_id: Option<Arc<String>>,
    language: Option<Arc<String>>,
    source_path: Option<Arc<PathBuf>>,
}

#[derive(Debug, Clone)]
pub struct ValidatedState {
    pub(crate) site: Arc<String>,
    pub(crate) contest_id: Arc<String>,
    pub(crate) problem_id: Arc<String>,
    pub(crate) language: Arc<String>,
    pub(crate) source_path: Arc<PathBuf>,
}

// 状態遷移の型安全性を向上させるための新しい型
#[derive(Debug, Clone)]
pub enum StateTransition {
    SetSite(String),
    SetContestId(String),
    SetProblemId(String),
    SetLanguage(String),
    SetSourcePath(PathBuf),
}

impl ContestState {
    pub fn new() -> Self {
        Self {
            site: None,
            contest_id: None,
            problem_id: None,
            language: None,
            source_path: None,
        }
    }

    pub fn site(&self) -> Option<&str> {
        self.site.as_ref().map(|s| s.as_str())
    }

    pub fn contest_id(&self) -> Option<&str> {
        self.contest_id.as_ref().map(|s| s.as_str())
    }

    pub fn problem_id(&self) -> Option<&str> {
        self.problem_id.as_ref().map(|s| s.as_str())
    }

    pub fn language(&self) -> Option<&str> {
        self.language.as_ref().map(|s| s.as_str())
    }

    pub fn source_path(&self) -> Option<&PathBuf> {
        self.source_path.as_ref().map(|p| p.as_ref())
    }

    pub fn apply_transition(self, transition: StateTransition) -> Self {
        match transition {
            StateTransition::SetSite(site) => self.with_site(site),
            StateTransition::SetContestId(id) => self.with_contest_id(id),
            StateTransition::SetProblemId(id) => self.with_problem_id(id),
            StateTransition::SetLanguage(lang) => self.with_language(lang),
            StateTransition::SetSourcePath(path) => self.with_source_path(path),
        }
    }

    pub fn validate(&self) -> Result<ValidatedState> {
        let site = self.site.clone()
            .ok_or_else(|| contest_error(ContestErrorKind::NotFound, "サイトが指定されていません"))?;
        
        let contest_id = self.contest_id.clone()
            .ok_or_else(|| contest_error(ContestErrorKind::NotFound, "コンテストIDが指定されていません"))?;
        
        let problem_id = self.problem_id.clone()
            .ok_or_else(|| contest_error(ContestErrorKind::NotFound, "問題IDが指定されていません"))?;
        
        let language = self.language.clone()
            .ok_or_else(|| contest_error(ContestErrorKind::NotFound, "言語が指定されていません"))?;
        
        let source_path = self.source_path.clone()
            .ok_or_else(|| contest_error(ContestErrorKind::NotFound, "ソースパスが指定されていません"))?;

        // 拡張されたバリデーションルール
        if site.is_empty() {
            return Err(contest_error(ContestErrorKind::Invalid, "サイトが空です"));
        }
        if contest_id.is_empty() {
            return Err(contest_error(ContestErrorKind::Invalid, "コンテストIDが空です"));
        }
        if problem_id.is_empty() {
            return Err(contest_error(ContestErrorKind::Invalid, "問題IDが空です"));
        }
        if language.is_empty() {
            return Err(contest_error(ContestErrorKind::Invalid, "言語が空です"));
        }

        // パスのバリデーション
        if !source_path.exists() {
            return Err(contest_error(ContestErrorKind::Invalid, "指定されたソースパスが存在しません"));
        }
        if !source_path.is_file() {
            return Err(contest_error(ContestErrorKind::Invalid, "指定されたソースパスはファイルではありません"));
        }

        Ok(ValidatedState {
            site,
            contest_id,
            problem_id,
            language,
            source_path,
        })
    }

    pub fn with_site<T: Into<String>>(self, site: T) -> Self {
        Self {
            site: Some(Arc::new(site.into())),
            contest_id: self.contest_id,
            problem_id: self.problem_id,
            language: self.language,
            source_path: self.source_path,
        }
    }

    pub fn with_contest_id<T: Into<String>>(self, contest_id: T) -> Self {
        Self {
            site: self.site,
            contest_id: Some(Arc::new(contest_id.into())),
            problem_id: self.problem_id,
            language: self.language,
            source_path: self.source_path,
        }
    }

    pub fn with_problem_id<T: Into<String>>(self, problem_id: T) -> Self {
        Self {
            site: self.site,
            contest_id: self.contest_id,
            problem_id: Some(Arc::new(problem_id.into())),
            language: self.language,
            source_path: self.source_path,
        }
    }

    pub fn with_language<T: Into<String>>(self, language: T) -> Self {
        Self {
            site: self.site,
            contest_id: self.contest_id,
            problem_id: self.problem_id,
            language: Some(Arc::new(language.into())),
            source_path: self.source_path,
        }
    }

    pub fn with_source_path<T: Into<PathBuf>>(self, source_path: T) -> Self {
        Self {
            site: self.site,
            contest_id: self.contest_id,
            problem_id: self.problem_id,
            language: self.language,
            source_path: Some(Arc::new(source_path.into())),
        }
    }
}

impl ValidatedState {
    pub fn site(&self) -> &str {
        &self.site
    }

    pub fn contest_id(&self) -> &str {
        &self.contest_id
    }

    pub fn problem_id(&self) -> &str {
        &self.problem_id
    }

    pub fn language(&self) -> &str {
        &self.language
    }

    pub fn source_path(&self) -> &PathBuf {
        &self.source_path
    }

    pub fn try_update(&self, transition: StateTransition) -> Result<ValidatedState> {
        let mut new_state = ContestState::new()
            .with_site(self.site.as_ref().clone())
            .with_contest_id(self.contest_id.as_ref().clone())
            .with_problem_id(self.problem_id.as_ref().clone())
            .with_language(self.language.as_ref().clone())
            .with_source_path(self.source_path.as_ref().clone());

        new_state = new_state.apply_transition(transition);
        new_state.validate()
    }
}

impl PartialEq for ValidatedState {
    fn eq(&self, other: &Self) -> bool {
        self.site == other.site &&
        self.contest_id == other.contest_id &&
        self.problem_id == other.problem_id &&
        self.language == other.language &&
        self.source_path == other.source_path
    }
}

impl Eq for ValidatedState {} 