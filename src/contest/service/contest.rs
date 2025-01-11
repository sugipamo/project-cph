use anyhow::{Result as AnyhowResult, anyhow};
use crate::contest::model::{Contest, TestCase};
use crate::fs::manager::Manager;
use crate::message::contest;

#[derive(Clone, Default)]
pub struct Service {
    site: Option<String>,
    contest_id: Option<String>,
    problem_id: Option<String>,
    language: Option<String>,
    url: Option<String>,
    file_manager: Option<Manager>,
}

// 状態遷移を表現する型
#[derive(Debug, Clone)]
pub enum ServiceTransition {
    Site(String),
    ContestId(String),
    ProblemId(String),
    TestCase(TestCase),
    FileManager(Manager),
}

impl Service {
    /// 新しいサービスインスタンスを作成します
    ///
    /// # Returns
    /// * `Result<Self>` - 作成されたサービスインスタンス
    ///
    /// # Errors
    /// * 設定の読み込みに失敗した場合
    pub fn new() -> AnyhowResult<Self> {
        Ok(Self::default())
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
            ServiceTransition::Site(site) => self.with_site(site),
            ServiceTransition::ContestId(id) => self.with_contest_id(id),
            ServiceTransition::ProblemId(id) => self.with_problem_id(id),
            ServiceTransition::TestCase(test_case) => self.with_test_case(test_case),
            ServiceTransition::FileManager(manager) => self.with_file_manager(manager),
        }
    }

    /// Validates site field
    /// 
    /// # Errors
    /// 
    /// Returns an error if site is not set
    pub fn validate_site(&self) -> AnyhowResult<()> {
        self.site.as_ref()
            .ok_or_else(|| anyhow!(contest::error("resource_not_found", "サイトが指定されていません")))
            .map(|_| ())
    }

    /// Validates language field
    /// 
    /// # Errors
    /// 
    /// Returns an error if language is not set
    pub fn validate_language(&self) -> AnyhowResult<()> {
        self.language.as_ref()
            .ok_or_else(|| anyhow!(contest::error("resource_not_found", "言語が指定されていません")))
            .map(|_| ())
    }

    /// Validates `contest_id` field
    /// 
    /// # Errors
    /// 
    /// Returns an error if `contest_id` is not set
    pub fn validate_contest_id(&self) -> AnyhowResult<()> {
        self.contest_id.as_ref()
            .ok_or_else(|| anyhow!(contest::error("resource_not_found", "コンテストIDが指定されていません")))
            .map(|_| ())
    }

    /// Validates `problem_id` field
    /// 
    /// # Errors
    /// 
    /// Returns an error if `problem_id` is not set
    pub fn validate_problem_id(&self) -> AnyhowResult<()> {
        self.problem_id.as_ref()
            .ok_or_else(|| anyhow!(contest::error("resource_not_found", "問題IDが指定されていません")))
            .map(|_| ())
    }

    /// Validates url field
    /// 
    /// # Errors
    /// 
    /// Returns an error if url is not set
    pub fn validate_url(&self) -> AnyhowResult<()> {
        self.url.as_ref()
            .ok_or_else(|| anyhow!(contest::error("resource_not_found", "URLが指定されていません")))
            .map(|_| ())
    }

    /// Validates `file_manager` field
    /// 
    /// # Errors
    /// 
    /// Returns an error if `file_manager` is not set
    pub fn validate_file_manager(&self) -> AnyhowResult<()> {
        self.file_manager.as_ref()
            .ok_or_else(|| anyhow!(contest::error("resource_not_found", "FileManagerが設定されていません")))
            .map(|_| ())
    }

    /// Validates all fields
    /// 
    /// # Errors
    /// 
    /// Returns an error if any field validation fails
    pub fn validate_all(&self) -> AnyhowResult<()> {
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

    #[must_use]
    pub fn with_test_case(self, _test_case: TestCase) -> Self {
        // テストケースは状態に影響を与えないため、そのまま返す
        self
    }

    /// Builds a Contest instance and returns it with the `FileManager`
    /// 
    /// # Errors
    /// 
    /// Returns an error if:
    /// - Any field validation fails
    /// - Workspace creation fails
    #[must_use = "この関数はContestインスタンスとManagerを返します"]
    pub fn build(self) -> AnyhowResult<(Contest, Manager)> {
        self.validate_all()?;
        
        let site = self.site.ok_or_else(|| anyhow!(contest::error("resource_not_found", "サイトが設定されていません")))?;
        let contest_id = self.contest_id.ok_or_else(|| anyhow!(contest::error("resource_not_found", "コンテストIDが設定されていません")))?;
        let problem_id = self.problem_id.ok_or_else(|| anyhow!(contest::error("resource_not_found", "問題IDが設定されていません")))?;
        let language = self.language.ok_or_else(|| anyhow!(contest::error("resource_not_found", "言語が設定されていません")))?;
        let url = self.url.ok_or_else(|| anyhow!(contest::error("resource_not_found", "URLが設定されていません")))?;
        let file_manager = self.file_manager.ok_or_else(|| anyhow!(contest::error("resource_not_found", "FileManagerが設定されていません")))?;

        let contest = Contest::new(
            site,
            contest_id,
            problem_id,
            language,
            url,
        );

        Ok((contest, file_manager))
    }

    /// コンテストを開きます
    /// 
    /// # Arguments
    /// * `site` - サイト名
    /// * `contest_id` - コンテストID
    /// * `problem_id` - 問題ID
    /// * `template_dir` - テンプレートディレクトリ
    /// * `active_dir` - アクティブディレクトリ
    /// 
    /// # Errors
    /// 
    /// - ディレクトリの作成に失敗した場合
    /// - ファイルのコピーに失敗した場合
    /// - 問題情報のダウンロードに失敗した場合
    pub fn open_with_config(
        &self,
        site: &str,
        contest_id: &str,
        problem_id: &str,
        template_dir: &str,
        active_dir: &str,
    ) -> AnyhowResult<()> {
        // アクティブディレクトリのパスを構築
        let contest_path = format!("{active_dir}/{site}/{contest_id}");
        let problem_path = format!("{contest_path}/{problem_id}");

        // ファイルマネージャーを作成
        let mut manager = Manager::new(&problem_path);

        // ディレクトリが存在しない場合は作成
        if !manager.exists("")? {
            manager = manager.create_dir("")?;
        }

        // テンプレートファイルをコピー
        let template_path = format!("{template_dir}/main.rs");
        let template_content = std::fs::read_to_string(template_path)
            .map_err(|e| anyhow::anyhow!("テンプレートファイルの読み込みに失敗しました: {e}"))?;

        // ファイルを書き込み
        manager.write_file("main.rs", template_content)?;

        Ok(())
    }

    /// 提出を行います
    /// 
    /// # Arguments
    /// 
    /// * `contest` - コンテスト情報
    /// 
    /// # Errors
    /// 
    /// - 提出に失敗した場合
    pub fn submit(&self, contest: &Contest) -> AnyhowResult<()> {
        println!("{}", contest::hint("optimize_code", format!("提出を行います: contest={contest:?}")));
        Ok(())
    }
} 