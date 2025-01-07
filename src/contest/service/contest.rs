use std::path::PathBuf;
use crate::error::Result;
use crate::error::contest::ContestErrorKind;
use crate::contest::error::contest_error;
use crate::contest::model::Contest;

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

    pub fn with_site(mut self, site: impl Into<String>) -> Self {
        self.site = Some(site.into());
        self
    }

    pub fn with_contest_id(mut self, contest_id: impl Into<String>) -> Self {
        self.contest_id = Some(contest_id.into());
        self
    }

    pub fn with_problem_id(mut self, problem_id: impl Into<String>) -> Self {
        self.problem_id = Some(problem_id.into());
        self
    }

    pub fn with_language(mut self, language: impl Into<String>) -> Self {
        self.language = Some(language.into());
        self
    }

    pub fn with_url(mut self, url: impl Into<String>) -> Self {
        self.url = Some(url.into());
        self
    }

    pub fn build(self) -> Result<Contest> {
        self.validate_site()?;
        self.validate_contest_id()?;
        self.validate_problem_id()?;
        self.validate_language()?;
        self.validate_url()?;

        Ok(Contest {
            id: self.contest_id.clone().unwrap(),
            name: format!("{} {}", self.site.clone().unwrap(), self.problem_id.clone().unwrap()),
            url: self.url.unwrap(),
            site: self.site.unwrap(),
            contest_id: self.contest_id.unwrap(),
            problem_id: self.problem_id.unwrap(),
            language: self.language.unwrap(),
        })
    }
} 