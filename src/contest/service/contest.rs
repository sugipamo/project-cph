use std::borrow::Cow;
use crate::error::Result;
use crate::error::contest::ContestErrorKind;
use crate::contest::error::contest_error;
use crate::contest::model::Contest;

#[derive(Clone)]
pub struct ContestService {
    site: Option<String>,
    contest_id: Option<String>,
    problem_id: Option<String>,
    language: Option<String>,
    url: Option<String>,
}

impl ContestService {
    pub fn new() -> Self {
        Self {
            site: None,
            contest_id: None,
            problem_id: None,
            language: None,
            url: None,
        }
    }

    // アクセサメソッド
    pub fn site(&self) -> Option<&str> {
        self.site.as_deref()
    }

    pub fn contest_id(&self) -> Option<&str> {
        self.contest_id.as_deref()
    }

    pub fn problem_id(&self) -> Option<&str> {
        self.problem_id.as_deref()
    }

    pub fn language(&self) -> Option<&str> {
        self.language.as_deref()
    }

    pub fn url(&self) -> Option<&str> {
        self.url.as_deref()
    }

    // バリデーションメソッド
    pub fn validate_site(&self) -> Result<()> {
        if self.site.is_none() {
            return Err(contest_error(
                ContestErrorKind::NotFound,
                "サイトが指定されていません"
            ));
        }
        Ok(())
    }

    pub fn validate_language(&self) -> Result<()> {
        if self.language.is_none() {
            return Err(contest_error(
                ContestErrorKind::NotFound,
                "言語が指定されていません"
            ));
        }
        Ok(())
    }

    pub fn validate_contest_id(&self) -> Result<()> {
        if self.contest_id.is_none() {
            return Err(contest_error(
                ContestErrorKind::NotFound,
                "コンテストIDが指定されていません"
            ));
        }
        Ok(())
    }

    pub fn validate_problem_id(&self) -> Result<()> {
        if self.problem_id.is_none() {
            return Err(contest_error(
                ContestErrorKind::NotFound,
                "問題IDが指定されていません"
            ));
        }
        Ok(())
    }

    pub fn validate_url(&self) -> Result<()> {
        if self.url.is_none() {
            return Err(contest_error(
                ContestErrorKind::NotFound,
                "URLが指定されていません"
            ));
        }
        Ok(())
    }

    // 全フィールドの一括バリデーション
    pub fn validate_all(&self) -> Result<()> {
        self.validate_site()?;
        self.validate_contest_id()?;
        self.validate_problem_id()?;
        self.validate_language()?;
        self.validate_url()?;
        Ok(())
    }

    // イミュータブルなビルダーメソッド
    pub fn with_site<T: Into<String>>(self, site: T) -> Self {
        Self {
            site: Some(site.into()),
            ..self
        }
    }

    pub fn with_contest_id<T: Into<String>>(self, contest_id: T) -> Self {
        Self {
            contest_id: Some(contest_id.into()),
            ..self
        }
    }

    pub fn with_problem_id<T: Into<String>>(self, problem_id: T) -> Self {
        Self {
            problem_id: Some(problem_id.into()),
            ..self
        }
    }

    pub fn with_language<T: Into<String>>(self, language: T) -> Self {
        Self {
            language: Some(language.into()),
            ..self
        }
    }

    pub fn with_url<T: Into<String>>(self, url: T) -> Self {
        Self {
            url: Some(url.into()),
            ..self
        }
    }

    pub fn build(self) -> Result<Contest> {
        self.validate_all()?;
        
        Ok(Contest::new(
            self.site.unwrap(),
            self.contest_id.unwrap(),
            self.problem_id.unwrap(),
            self.language.unwrap(),
            self.url.unwrap(),
        ))
    }
} 