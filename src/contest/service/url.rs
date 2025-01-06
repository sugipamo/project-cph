use crate::contest::error::{ContestError, ContestResult};
use crate::config::Config;

pub struct UrlService {
    config: Config,
    site: String,
}

impl UrlService {
    pub fn new(config: Config, site: String) -> Self {
        Self { config, site }
    }

    pub fn get_contest_url(&self, contest_id: &str) -> ContestResult<String> {
        self.get_url(contest_id, "contest")
    }

    pub fn get_problem_url(&self, contest_id: &str, problem_id: &str) -> ContestResult<String> {
        let _contest_url = self.get_contest_url(contest_id)?;
        let problem_pattern = self.config.get::<String>(&format!("sites.{}.problem_url", self.site))
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let url = problem_pattern
            .replace("{contest_id}", contest_id)
            .replace("{problem_id}", problem_id);

        Ok(url)
    }

    fn get_url(&self, contest_id: &str, url_type: &str) -> ContestResult<String> {
        let pattern = self.config.get::<String>(&format!("sites.{}.{}_url", self.site, url_type))
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let url = pattern.replace("{contest_id}", contest_id);
        Ok(url)
    }
} 