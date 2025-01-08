use anyhow::{Result, anyhow};

pub struct Service {
    site: Option<String>,
    contest_id: Option<String>,
    problem_id: Option<String>,
}

impl Default for Service {
    fn default() -> Self {
        Self::new()
    }
}

impl Service {
    #[must_use = "この関数は新しいServiceインスタンスを返します"]
    pub const fn new() -> Self {
        Self {
            site: None,
            contest_id: None,
            problem_id: None,
        }
    }

    /// サイトの指定を検証します。
    /// 
    /// # Errors
    /// - サイトが指定されていない場合
    pub fn validate_site(&self) -> Result<()> {
        if self.site.is_none() {
            return Err(anyhow!("サイトが指定されていません"));
        }
        Ok(())
    }

    /// コンテストIDの指定を検証します。
    /// 
    /// # Errors
    /// - コンテストIDが指定されていない場合
    pub fn validate_contest_id(&self) -> Result<()> {
        if self.contest_id.is_none() {
            return Err(anyhow!("コンテストIDが指定されていません"));
        }
        Ok(())
    }

    /// 問題IDの指定を検証します。
    /// 
    /// # Errors
    /// - 問題IDが指定されていない場合
    pub fn validate_problem_id(&self) -> Result<()> {
        if self.problem_id.is_none() {
            return Err(anyhow!("問題IDが指定されていません"));
        }
        Ok(())
    }

    /// コンテストのURLを取得します。
    /// 
    /// # Errors
    /// - サイトが指定されていない場合
    /// - コンテストIDが指定されていない場合
    /// - 未対応のサイトが指定された場合
    /// 
    /// # Panics
    /// 
    /// - `内部状態が不整合な場合（validate_site()が成功したのにsiteがNoneの場合など）`
    #[must_use = "この関数はコンテストのURLを返します"]
    pub fn get_contest_url(&self) -> Result<String> {
        self.validate_site()?;
        self.validate_contest_id()?;

        let site = self.site.as_deref().expect("サイトが指定されていません");
        let contest_id = self.contest_id.as_ref().expect("コンテストIDが指定されていません");

        match site {
            "atcoder" => Ok(format!(
                "https://atcoder.jp/contests/{contest_id}"
            )),
            _ => Err(anyhow!("未対応のサイトです: {site}")),
        }
    }

    /// 問題のURLを取得します。
    /// 
    /// # Errors
    /// - サイトが指定されていない場合
    /// - コンテストIDが指定されていない場合
    /// - 問題IDが指定されていない場合
    /// - 未対応のサイトが指定された場合
    /// 
    /// # Panics
    /// 
    /// - `内部状態が不整合な場合（validate_site()が成功したのにsiteがNoneの場合など）`
    #[must_use = "この関数は�題のURLを返します"]
    pub fn get_problem_url(&self) -> Result<String> {
        self.validate_site()?;
        self.validate_contest_id()?;
        self.validate_problem_id()?;

        let site = self.site.as_deref().expect("サイトが指定されていません");
        let contest_id = self.contest_id.as_ref().expect("コンテストIDが指定されていません");
        let problem_id = self.problem_id.as_ref().expect("問題IDが指定されていません");

        match site {
            "atcoder" => Ok(format!(
                "https://atcoder.jp/contests/{contest_id}/tasks/{problem_id}"
            )),
            _ => Err(anyhow!("未対応のサイトです: {site}")),
        }
    }

    #[must_use = "この関数は新しいServiceインスタンスを返します"]
    pub fn with_site(mut self, site: impl Into<String>) -> Self {
        self.site = Some(site.into());
        self
    }

    #[must_use = "この関数は新しいServiceインスタンスを返します"]
    pub fn with_contest_id(mut self, contest_id: impl Into<String>) -> Self {
        self.contest_id = Some(contest_id.into());
        self
    }

    #[must_use = "この関数は新しいServiceインスタンスを返します"]
    pub fn with_problem_id(mut self, problem_id: impl Into<String>) -> Self {
        self.problem_id = Some(problem_id.into());
        self
    }
} 