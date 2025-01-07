use crate::error::Result;
use crate::error::contest::ContestErrorKind;
use crate::contest::error::contest_error;

pub struct UrlService {
    site: Option<String>,
    contest_id: Option<String>,
    problem_id: Option<String>,
}

impl UrlService {
    pub fn new() -> Self {
        Self {
            site: None,
            contest_id: None,
            problem_id: None,
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

    pub fn get_contest_url(&self) -> Result<String> {
        self.validate_site()?;
        self.validate_contest_id()?;

        match self.site.as_deref().unwrap() {
            "atcoder" => Ok(format!(
                "https://atcoder.jp/contests/{}",
                self.contest_id.as_ref().unwrap()
            )),
            _ => Err(contest_error(
                ContestErrorKind::InvalidUrl,
                format!("未対応のサイトです: {}", self.site.as_ref().unwrap())
            )),
        }
    }

    pub fn get_problem_url(&self) -> Result<String> {
        self.validate_site()?;
        self.validate_contest_id()?;
        self.validate_problem_id()?;

        match self.site.as_deref().unwrap() {
            "atcoder" => Ok(format!(
                "https://atcoder.jp/contests/{}/tasks/{}",
                self.contest_id.as_ref().unwrap(),
                self.problem_id.as_ref().unwrap()
            )),
            _ => Err(contest_error(
                ContestErrorKind::InvalidUrl,
                format!("未対応のサイトです: {}", self.site.as_ref().unwrap())
            )),
        }
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
} 