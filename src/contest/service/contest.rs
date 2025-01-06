use std::path::PathBuf;
use crate::error::Result;
use crate::contest::error::{config_err, site_err, language_err};
use crate::contest::model::ContestState;

pub struct ContestService {
    state: ContestState,
}

impl ContestService {
    pub fn new(
        site: String,
        contest_id: String,
        problem_id: String,
        language: String,
        source_path: PathBuf,
    ) -> Result<Self> {
        let state = ContestState::new(site, contest_id, problem_id, language, source_path)?;
        Ok(Self { state })
    }

    pub fn get_state(&self) -> &ContestState {
        &self.state
    }

    pub fn update_site(&mut self, site: String) -> Result<()> {
        if site.is_empty() {
            return Err(site_err("サイトが指定されていません".to_string()));
        }
        let state = ContestState::new(
            site,
            self.state.contest_id.clone(),
            self.state.problem_id.clone(),
            self.state.language.clone(),
            self.state.source_path.clone(),
        )?;
        self.state = state;
        Ok(())
    }

    pub fn update_language(&mut self, language: String) -> Result<()> {
        if language.is_empty() {
            return Err(language_err("言語が指定されていません".to_string()));
        }
        let state = ContestState::new(
            self.state.site.clone(),
            self.state.contest_id.clone(),
            self.state.problem_id.clone(),
            language,
            self.state.source_path.clone(),
        )?;
        self.state = state;
        Ok(())
    }

    pub fn update_problem(&mut self, problem_id: String) -> Result<()> {
        if problem_id.is_empty() {
            return Err(config_err("問題IDが指定されていません".to_string()));
        }
        let state = ContestState::new(
            self.state.site.clone(),
            self.state.contest_id.clone(),
            problem_id,
            self.state.language.clone(),
            self.state.source_path.clone(),
        )?;
        self.state = state;
        Ok(())
    }
} 