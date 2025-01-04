use crate::config::Config;
use crate::contest::error::{Result, ContestError};

/// URL生成を担当する構造体
#[derive(Debug)]
pub struct UrlGenerator {
    /// サイトID
    site: String,
    /// コンテストID
    contest: String,
    /// 設定情報
    config: Config,
}

impl UrlGenerator {
    /// 新しいURLジェネレータを作成
    pub fn new(site: String, contest: String, config: Config) -> Self {
        Self {
            site,
            contest,
            config,
        }
    }

    /// サイトのURLを生成
    fn get_site_url(&self, url_type: &str, problem_id: &str) -> Result<String> {
        let pattern = self.config.get::<String>(&format!("sites.{}.{}_url", self.site, url_type))
            .map_err(|e| ContestError::Config {
                message: format!("サイトURLパターンの取得に失敗: {}", e),
                source: None,
            })?;
        
        let site_url = self.config.get::<String>(&format!("sites.{}.url", self.site))
            .map_err(|e| ContestError::Config {
                message: format!("サイトURLの取得に失敗: {}", e),
                source: None,
            })?;

        Ok(pattern
            .replace("{url}", &site_url)
            .replace("{contest}", &self.contest)
            .replace("{problem}", problem_id))
    }

    /// 問題のURLを取得
    pub fn get_problem_url(&self, problem_id: &str) -> Result<String> {
        self.get_site_url("problem", problem_id)
    }

    /// 提出のURLを取得
    pub fn get_submit_url(&self, problem_id: &str) -> Result<String> {
        self.get_site_url("submit", problem_id)
    }
} 