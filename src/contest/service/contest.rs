use anyhow::{Result, anyhow};
use crate::config::Config;
use crate::contest::model::{Contest, TestCase};
use crate::fs::manager::FileManager;

#[derive(Clone)]
pub struct ContestService {
    site: Option<String>,
    contest_id: Option<String>,
    problem_id: Option<String>,
    language: Option<String>,
    url: Option<String>,
    file_manager: Option<FileManager>,
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
    SetFileManager(FileManager),
}

impl ContestService {
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

    // 状態遷移を適用するメソッド
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

    // バリデーションメソッド
    pub fn validate_site(&self) -> Result<()> {
        if self.site.is_none() {
            return Err(anyhow!("サイトが指定されていません"));
        }
        Ok(())
    }

    pub fn validate_language(&self) -> Result<()> {
        if self.language.is_none() {
            return Err(anyhow!("言語が指定されていません"));
        }
        Ok(())
    }

    pub fn validate_contest_id(&self) -> Result<()> {
        if self.contest_id.is_none() {
            return Err(anyhow!("コンテストIDが指定されていません"));
        }
        Ok(())
    }

    pub fn validate_problem_id(&self) -> Result<()> {
        if self.problem_id.is_none() {
            return Err(anyhow!("問題IDが指定されていません"));
        }
        Ok(())
    }

    pub fn validate_url(&self) -> Result<()> {
        if self.url.is_none() {
            return Err(anyhow!("URLが指定されていません"));
        }
        Ok(())
    }

    pub fn validate_file_manager(&self) -> Result<()> {
        if self.file_manager.is_none() {
            return Err(anyhow!("FileManagerが設定されていません"));
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
        self.validate_file_manager()?;
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

    pub fn with_file_manager(self, file_manager: FileManager) -> Self {
        Self {
            file_manager: Some(file_manager),
            ..self
        }
    }

    pub fn build(self) -> Result<(Contest, FileManager)> {
        self.validate_all()?;
        
        let contest = Contest::new(
            self.site.unwrap(),
            self.contest_id.unwrap(),
            self.problem_id.unwrap(),
            self.language.unwrap(),
            self.url.unwrap(),
        );

        let file_manager = self.file_manager.unwrap();
        let file_manager = contest.create_workspace(file_manager)?;

        Ok((contest, file_manager))
    }

    // テストケースの保存をイミュータブルに処理
    fn save_test_cases(contest: &Contest, file_manager: FileManager, test_cases: &[TestCase]) -> Result<FileManager> {
        test_cases.iter().enumerate().try_fold(file_manager, |manager, (index, test_case)| {
            contest.save_test_case(manager, test_case, index)
        })
    }

    pub fn setup_contest(self, template: &str, test_cases: &[TestCase]) -> Result<(Contest, FileManager)> {
        let (contest, file_manager) = self.build()?;
        let file_manager = contest.save_template(file_manager, template)?;
        let file_manager = Self::save_test_cases(&contest, file_manager, test_cases)?;
        Ok((contest, file_manager))
    }

    // コマンド実行用のメソッド
    pub fn open(&self, site: String, contest_id: Option<String>, problem_id: Option<String>) -> Result<()> {
        // TODO: 実際のブラウザでの問題ページを開く処理を実装
        println!("問題を開きます: site={}, contest={:?}, problem={:?}", 
            site, contest_id, problem_id);
        Ok(())
    }

    pub fn submit(&self, contest: &Contest) -> Result<()> {
        // TODO: 実際の提出処理を実装
        println!("提出を行います: contest={:?}", contest);
        Ok(())
    }
} 