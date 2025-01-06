use crate::error::Result;
use crate::contest::error::site_err;

pub struct UrlService {
    site: String,
}

impl UrlService {
    pub fn new(site: String) -> Result<Self> {
        if site.is_empty() {
            return Err(site_err("サイトが指定されていません".to_string()));
        }
        Ok(Self { site })
    }

    pub fn get_contest_url(&self, contest_id: &str) -> Result<String> {
        if contest_id.is_empty() {
            return Err(site_err("コンテストIDが指定されていません".to_string()));
        }

        let url = match self.site.as_str() {
            "atcoder" => format!("https://atcoder.jp/contests/{}", contest_id),
            "codeforces" => format!("https://codeforces.com/contest/{}", contest_id),
            _ => return Err(site_err(format!("未対応のサイトです: {}", self.site))),
        };

        Ok(url)
    }

    pub fn get_problem_url(&self, contest_id: &str, problem_id: &str) -> Result<String> {
        if contest_id.is_empty() {
            return Err(site_err("コンテストIDが指定されていません".to_string()));
        }
        if problem_id.is_empty() {
            return Err(site_err("問題IDが指定されていません".to_string()));
        }

        let url = match self.site.as_str() {
            "atcoder" => format!("https://atcoder.jp/contests/{}/tasks/{}", contest_id, problem_id),
            "codeforces" => format!("https://codeforces.com/contest/{}/problem/{}", contest_id, problem_id),
            _ => return Err(site_err(format!("未対応のサイトです: {}", self.site))),
        };

        Ok(url)
    }
} 