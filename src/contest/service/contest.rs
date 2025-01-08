use anyhow::{Result, anyhow};
use crate::config::Config;
use crate::contest::model::{Contest, TestCase};
use crate::fs::manager::Manager;

#[derive(Clone)]
pub struct Service {
    site: Option<String>,
    contest_id: Option<String>,
    problem_id: Option<String>,
    language: Option<String>,
    url: Option<String>,
    file_manager: Option<Manager>,
    #[allow(dead_code)]
    config: Config,
}

// 状態遷移を表現する型
#[derive(Debug, Clone)]
pub enum ServiceTransition {
    SetSite(String),
    SetContestId(String),
    SetProblemId(String),
    SetLanguage(String),
    SetUrl(String),
    SetFileManager(Manager),
}

impl Service {
    /// Creates a new Service instance
    /// 
    /// # Errors
    /// 
    /// Currently this function cannot fail, but returns Result for consistency
    #[must_use]
    pub fn new(config: &Config) -> Result<Self> {
        Ok(Self {
            site: None,
            contest_id: None,
            problem_id: None,
            language: None,
            url: None,
            file_manager: None,
            config: config.clone(),
        })
    }

    // アクセサメソッド
    #[must_use]
    pub fn site(&self) -> Option<&str> {
        self.site.as_deref()
    }

    #[must_use]
    pub fn contest_id(&self) -> Option<&str> {
        self.contest_id.as_deref()
    }

    #[must_use]
    pub fn problem_id(&self) -> Option<&str> {
        self.problem_id.as_deref()
    }

    #[must_use]
    pub fn language(&self) -> Option<&str> {
        self.language.as_deref()
    }

    #[must_use]
    pub fn url(&self) -> Option<&str> {
        self.url.as_deref()
    }

    // 状態遷移を適用するメソッド
    #[must_use]
    pub fn apply_transition(self, transition: ServiceTransition) -> Self {
        match transition {
            ServiceTransition::SetSite(site) => self.with_site(site),
            ServiceTransition::SetContestId(id) => self.with_contest_id(id),
            ServiceTransition::SetProblemId(id) => self.with_problem_id(id),
            ServiceTransition::SetLanguage(lang) => self.with_language(lang),
            ServiceTransition::SetUrl(url) => self.with_url(url),
            ServiceTransition::SetFileManager(manager) => self.with_file_manager(manager),
        }
    }

    /// Validates site field
    /// 
    /// # Errors
    /// 
    /// Returns an error if site is not set
    pub fn validate_site(&self) -> Result<()> {
        self.site.as_ref()
            .ok_or_else(|| anyhow!("サイトが指定されていません"))
            .map(|_| ())
    }

    /// Validates language field
    /// 
    /// # Errors
    /// 
    /// Returns an error if language is not set
    pub fn validate_language(&self) -> Result<()> {
        self.language.as_ref()
            .ok_or_else(|| anyhow!("言語が指定されていません"))
            .map(|_| ())
    }

    /// Validates contest_id field
    /// 
    /// # Errors
    /// 
    /// Returns an error if contest_id is not set
    pub fn validate_contest_id(&self) -> Result<()> {
        self.contest_id.as_ref()
            .ok_or_else(|| anyhow!("コンテストIDが指定されていません"))
            .map(|_| ())
    }

    /// Validates problem_id field
    /// 
    /// # Errors
    /// 
    /// Returns an error if problem_id is not set
    pub fn validate_problem_id(&self) -> Result<()> {
        self.problem_id.as_ref()
            .ok_or_else(|| anyhow!("問題IDが指定されていません"))
            .map(|_| ())
    }

    /// Validates url field
    /// 
    /// # Errors
    /// 
    /// Returns an error if url is not set
    pub fn validate_url(&self) -> Result<()> {
        self.url.as_ref()
            .ok_or_else(|| anyhow!("URLが指定されていません"))
            .map(|_| ())
    }

    /// Validates file_manager field
    /// 
    /// # Errors
    /// 
    /// Returns an error if file_manager is not set
    pub fn validate_file_manager(&self) -> Result<()> {
        self.file_manager.as_ref()
            .ok_or_else(|| anyhow!("FileManagerが設定されていません"))
            .map(|_| ())
    }

    /// Validates all fields
    /// 
    /// # Errors
    /// 
    /// Returns an error if any field validation fails
    pub fn validate_all(&self) -> Result<()> {
        self.validate_site()?;
        self.validate_contest_id()?;
        self.validate_problem_id()?;
        self.validate_language()?;
        self.validate_url()?;
        self.validate_file_manager()?;
        Ok(())
    }

    // イミュータブルなビルダーメソッド
    #[must_use]
    pub fn with_site<T: Into<String>>(self, site: T) -> Self {
        Self {
            site: Some(site.into()),
            ..self
        }
    }

    #[must_use]
    pub fn with_contest_id<T: Into<String>>(self, contest_id: T) -> Self {
        Self {
            contest_id: Some(contest_id.into()),
            ..self
        }
    }

    #[must_use]
    pub fn with_problem_id<T: Into<String>>(self, problem_id: T) -> Self {
        Self {
            problem_id: Some(problem_id.into()),
            ..self
        }
    }

    #[must_use]
    pub fn with_language<T: Into<String>>(self, language: T) -> Self {
        Self {
            language: Some(language.into()),
            ..self
        }
    }

    #[must_use]
    pub fn with_url<T: Into<String>>(self, url: T) -> Self {
        Self {
            url: Some(url.into()),
            ..self
        }
    }

    #[must_use]
    pub fn with_file_manager(self, file_manager: Manager) -> Self {
        Self {
            file_manager: Some(file_manager),
            ..self
        }
    }

    /// Builds a Contest instance and returns it with the FileManager
    /// 
    /// # Errors
    /// 
    /// Returns an error if:
    /// - Any field validation fails
    /// - Workspace creation fails
    #[must_use]
    pub fn build(self) -> Result<(Contest, Manager)> {
        self.validate_all()?;
        
        let site = self.site.ok_or_else(|| anyhow!("サイトが設定されていません"))?;
        let contest_id = self.contest_id.ok_or_else(|| anyhow!("コンテストIDが設定されていません"))?;
        let problem_id = self.problem_id.ok_or_else(|| anyhow!("問題IDが設定されていません"))?;
        let language = self.language.ok_or_else(|| anyhow!("言語が設定されていません"))?;
        let url = self.url.ok_or_else(|| anyhow!("URLが設定されていません"))?;
        let file_manager = self.file_manager.ok_or_else(|| anyhow!("FileManagerが設定されていません"))?;

        let contest = Contest::new(
            site,
            contest_id,
            problem_id,
            language,
            url,
        );

        let file_manager = contest.create_workspace(file_manager)?;

        Ok((contest, file_manager))
    }

    /// Saves test cases to the workspace
    /// 
    /// # Errors
    /// 
    /// Returns an error if saving any test case fails
    #[must_use]
    fn save_test_cases(contest: &Contest, file_manager: Manager, test_cases: &[TestCase]) -> Result<Manager> {
        test_cases.iter().enumerate().try_fold(file_manager, |manager, (index, test_case)| {
            contest.save_test_case(manager, test_case, index)
        })
    }

    /// Sets up a contest with template and test cases
    /// 
    /// # Errors
    /// 
    /// Returns an error if:
    /// - Building the contest fails
    /// - Saving template fails
    /// - Saving test cases fails
    #[must_use]
    pub fn setup_contest(self, template: &str, test_cases: &[TestCase]) -> Result<(Contest, Manager)> {
        let (contest, file_manager) = self.build()?;
        let file_manager = contest.save_template(file_manager, template)?;
        let file_manager = Self::save_test_cases(&contest, file_manager, test_cases)?;
        Ok((contest, file_manager))
    }

    /// Opens a problem in the browser
    /// 
    /// # Errors
    /// 
    /// Currently this function cannot fail, but returns Result for consistency
    pub fn open(&self, site: String, contest_id: Option<String>, problem_id: Option<String>) -> Result<()> {
        println!("問題を開きます: site={site}, contest={contest_id:?}, problem={problem_id:?}");
        Ok(())
    }

    /// Submits a solution for the contest
    /// 
    /// # Errors
    /// 
    /// Currently this function cannot fail, but returns Result for consistency
    pub fn submit(&self, contest: &Contest) -> Result<()> {
        println!("提出を行います: contest={contest:?}");
        Ok(())
    }
} 