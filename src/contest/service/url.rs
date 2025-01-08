use anyhow::{Result, anyhow};
use crate::message::contest;

/// URL生成を担当するトレイト
pub trait Generator: std::fmt::Debug {
    /// コンテストのURLを生成します
    fn contest_url(&self, contest_id: &str) -> String;

    /// 問題のURLを生成します
    fn problem_url(&self, contest_id: &str, problem_id: &str) -> String;
}

/// `AtCoder`のURL生成を担当する構造体
#[derive(Debug)]
pub struct AtCoderGenerator;

impl Generator for AtCoderGenerator {
    fn contest_url(&self, contest_id: &str) -> String {
        format!("https://atcoder.jp/contests/{contest_id}")
    }

    fn problem_url(&self, contest_id: &str, problem_id: &str) -> String {
        format!("https://atcoder.jp/contests/{contest_id}/tasks/{problem_id}")
    }
}

/// URL管理サービスを提供する構造体
#[derive(Debug)]
pub struct Service {
    site: Option<Box<dyn Generator>>,
    contest_id: Option<String>,
    problem_id: Option<String>,
}

impl Default for Service {
    fn default() -> Self {
        Self::new()
    }
}

impl Service {
    /// 新しいURL管理サービスを作成します
    ///
    /// # Returns
    /// * `Self` - 新しいURL管理サービスインスタンス
    #[must_use = "この関数は新しいURLServiceインスタンスを返します"]
    pub const fn new() -> Self {
        Self {
            site: None,
            contest_id: None,
            problem_id: None,
        }
    }

    /// サイトを設定します
    ///
    /// # Arguments
    /// * `site` - URL生成を担当する構造体
    ///
    /// # Returns
    /// * `Self` - 設定を変更したURL管理サービスインスタンス
    #[must_use = "この関数は新しいURLServiceインスタンスを返します"]
    pub fn with_site(mut self, site: Box<dyn Generator>) -> Self {
        self.site = Some(site);
        self
    }

    /// コンテストIDを設定します
    ///
    /// # Arguments
    /// * `contest_id` - コンテストID
    ///
    /// # Returns
    /// * `Self` - 設定を変更したURL管理サービスインスタンス
    #[must_use = "この関数は新しいURLServiceインスタンスを返します"]
    pub fn with_contest_id(mut self, contest_id: impl Into<String>) -> Self {
        self.contest_id = Some(contest_id.into());
        self
    }

    /// 問題IDを設定します
    ///
    /// # Arguments
    /// * `problem_id` - 問題ID
    ///
    /// # Returns
    /// * `Self` - 設定を変更したURL管理サービスインスタンス
    #[must_use = "この関数は新しいURLServiceインスタンスを返します"]
    pub fn with_problem_id(mut self, problem_id: impl Into<String>) -> Self {
        self.problem_id = Some(problem_id.into());
        self
    }

    /// コンテストのURLを取得します
    ///
    /// # Returns
    /// * `Result<String>` - コンテストのURL
    ///
    /// # Errors
    /// * サイトが設定されていない場合
    /// * コンテストIDが設定されていない場合
    /// * 内部状態が不整合な場合（`validate_site`が成功したのに`site`が`None`の場合など）
    pub fn get_contest_url(&self) -> Result<String> {
        self.validate_site()?;
        self.validate_contest_id()?;

        let site = self.site.as_ref()
            .ok_or_else(|| anyhow!(contest::error("url_error", "サイトが設定されていません")))?;
        let contest_id = self.contest_id.as_ref()
            .ok_or_else(|| anyhow!(contest::error("url_error", "コンテストIDが設定されていません")))?;

        Ok(site.contest_url(contest_id))
    }

    /// 問題のURLを取得します
    ///
    /// # Returns
    /// * `Result<String>` - 問題のURL
    ///
    /// # Errors
    /// * サイトが設定されていない場合
    /// * コンテストIDが設定されていない場合
    /// * 問題IDが設定されていない場合
    /// * 内部状態が不整合な場合（`validate_site`が成功したのに`site`が`None`の場合など）
    pub fn get_problem_url(&self) -> Result<String> {
        self.validate_site()?;
        self.validate_contest_id()?;
        self.validate_problem_id()?;

        let site = self.site.as_ref()
            .ok_or_else(|| anyhow!(contest::error("url_error", "サイトが設定されていません")))?;
        let contest_id = self.contest_id.as_ref()
            .ok_or_else(|| anyhow!(contest::error("url_error", "コンテストIDが設定されていません")))?;
        let problem_id = self.problem_id.as_ref()
            .ok_or_else(|| anyhow!(contest::error("url_error", "問題IDが設定されていません")))?;

        Ok(site.problem_url(contest_id, problem_id))
    }

    /// サイトの設定を検証します
    ///
    /// # Returns
    /// * `Result<()>` - 検証結果
    ///
    /// # Errors
    /// * サイトが設定されていない場合
    fn validate_site(&self) -> Result<()> {
        if self.site.is_none() {
            return Err(anyhow!(contest::error("url_error", "サイトが設定されていません")));
        }
        Ok(())
    }

    /// コンテストIDの設定を検証します
    ///
    /// # Returns
    /// * `Result<()>` - 検証結果
    ///
    /// # Errors
    /// * コンテストIDが設定されていない場合
    fn validate_contest_id(&self) -> Result<()> {
        if self.contest_id.is_none() {
            return Err(anyhow!(contest::error("url_error", "コンテストIDが設定されていません")));
        }
        Ok(())
    }

    /// 問題IDの設定を検証します
    ///
    /// # Returns
    /// * `Result<()>` - 検証結果
    ///
    /// # Errors
    /// * 問題IDが設定されていない場合
    fn validate_problem_id(&self) -> Result<()> {
        if self.problem_id.is_none() {
            return Err(anyhow!(contest::error("url_error", "問題IDが設定されていません")));
        }
        Ok(())
    }
} 