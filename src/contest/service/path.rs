use std::path::PathBuf;
use crate::config::Config;
use crate::contest::error::{ContestError, ContestResult};

pub struct PathService {
    config: Config,
}

impl PathService {
    pub fn new(config: Config) -> Self {
        Self { config }
    }

    pub fn get_test_dir(&self, problem_id: &str) -> ContestResult<PathBuf> {
        let default_lang = self.config
            .get::<String>("languages.default")
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let active_dir = self.config
            .get::<String>(&format!("languages.{}.contest_dir.active", default_lang))
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let test_dir = PathBuf::from(active_dir)
            .join("test")
            .join(problem_id);

        if !test_dir.exists() {
            std::fs::create_dir_all(&test_dir)
                .map_err(|e| ContestError::IO(e))?;
        }

        Ok(test_dir)
    }

    pub fn get_source_file(&self, problem_id: &str) -> ContestResult<PathBuf> {
        let default_lang = self.config
            .get::<String>("languages.default")
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let active_dir = self.config
            .get::<String>(&format!("languages.{}.contest_dir.active", default_lang))
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let source_dir = PathBuf::from(active_dir)
            .join("src");

        if !source_dir.exists() {
            std::fs::create_dir_all(&source_dir)
                .map_err(|e| ContestError::IO(e))?;
        }

        let extension = self.config
            .get::<String>(&format!("languages.{}.extension", default_lang))
            .map_err(|e| ContestError::Config(e.to_string()))?;

        Ok(source_dir.join(format!("{}.{}", problem_id, extension)))
    }
} 