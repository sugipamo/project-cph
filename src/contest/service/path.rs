use std::path::{Path, PathBuf};
use crate::contest::error::{ContestError, ContestResult};
use crate::config::Config;

pub struct PathService {
    config: Config,
}

impl PathService {
    pub fn new(config: Config) -> Self {
        Self { config }
    }

    pub fn get_template_path(&self, language: &str) -> ContestResult<PathBuf> {
        let template_dir = self.config.get::<String>(&format!("languages.{}.templates.directory", language))
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let template_base = self.config.get::<String>("system.contest_dir.template")
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let path = PathBuf::from(template_base).join(template_dir);
        if !path.exists() {
            std::fs::create_dir_all(&path)
                .map_err(|e| ContestError::Io(e))?;
        }

        Ok(path)
    }

    pub fn get_storage_path(&self, contest_id: &str) -> ContestResult<PathBuf> {
        let storage_base = self.config.get::<String>("system.contest_dir.storage")
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let path = PathBuf::from(storage_base).join(contest_id);
        if !path.exists() {
            std::fs::create_dir_all(&path)
                .map_err(|e| ContestError::Io(e))?;
        }

        Ok(path)
    }

    pub fn get_problem_path(&self, contest_id: &str, problem_id: &str, language: &str) -> ContestResult<PathBuf> {
        let storage_path = self.get_storage_path(contest_id)?;
        let extension = self.config.get::<String>(&format!("languages.{}.extension", language))
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let file_name = format!("{}.{}", problem_id, extension);
        Ok(storage_path.join(file_name))
    }

    pub fn get_test_path(&self, contest_id: &str, problem_id: &str) -> ContestResult<PathBuf> {
        let storage_path = self.get_storage_path(contest_id)?;
        Ok(storage_path.join("tests").join(problem_id))
    }

    pub fn ensure_directory(&self, path: &Path) -> ContestResult<()> {
        if !path.exists() {
            std::fs::create_dir_all(path)
                .map_err(|e| ContestError::Io(e))?;
        }
        Ok(())
    }
} 