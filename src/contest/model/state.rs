use std::path::PathBuf;
use crate::error::Result;
use crate::contest::error::config_err;

#[derive(Debug, Clone)]
pub struct ContestState {
    pub site: String,
    pub contest_id: String,
    pub problem_id: String,
    pub language: String,
    pub source_path: PathBuf,
}

impl ContestState {
    pub fn new(
        site: String,
        contest_id: String,
        problem_id: String,
        language: String,
        source_path: PathBuf,
    ) -> Result<Self> {
        if site.is_empty() {
            return Err(config_err("サイトが指定されていません".to_string()));
        }
        if contest_id.is_empty() {
            return Err(config_err("コンテストIDが指定されていません".to_string()));
        }
        if problem_id.is_empty() {
            return Err(config_err("問題IDが指定されていません".to_string()));
        }
        if language.is_empty() {
            return Err(config_err("言語が指定されていません".to_string()));
        }

        Ok(Self {
            site,
            contest_id,
            problem_id,
            language,
            source_path,
        })
    }
} 