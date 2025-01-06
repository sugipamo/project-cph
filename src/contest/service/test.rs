use std::path::PathBuf;
use crate::config::Config;
use crate::contest::error::{ContestError, ContestResult};
use crate::test::{TestCase, TestRunner};

pub struct TestService {
    config: Config,
}

impl TestService {
    pub fn new(config: Config) -> Self {
        Self { config }
    }

    pub async fn run_test(&self, problem_id: &str) -> ContestResult<Vec<bool>> {
        let test_dir = self.get_test_dir(problem_id)?;
        
        if !test_dir.exists() {
            std::fs::create_dir_all(&test_dir)
                .map_err(|e| ContestError::IO(e))?;
        }

        let mut results = Vec::new();
        let entries = std::fs::read_dir(&test_dir)
            .map_err(|e| ContestError::IO(e))?;

        for entry in entries {
            let entry = entry.map_err(|e| ContestError::IO(e))?;
            let path = entry.path();

            if path.is_file() && path.extension().map_or(false, |ext| ext == "in") {
                let test_case = self.load_test_case(&path)?;
                // TODO: 実際のテスト実行を実装
                results.push(true);
            }
        }

        Ok(results)
    }

    fn get_test_dir(&self, problem_id: &str) -> ContestResult<PathBuf> {
        let default_lang = self.config
            .get::<String>("languages.default")
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let active_dir = self.config
            .get::<String>(&format!("languages.{}.contest_dir.active", default_lang))
            .map_err(|e| ContestError::Config(e.to_string()))?;

        Ok(PathBuf::from(active_dir).join("test").join(problem_id))
    }

    fn load_test_case(&self, test_file: &PathBuf) -> ContestResult<TestCase> {
        let input = std::fs::read_to_string(test_file)
            .map_err(|e| ContestError::IO(e))?;

        let expected_path = test_file.with_extension("out");
        let expected = std::fs::read_to_string(&expected_path)
            .map_err(|e| ContestError::IO(e))?;

        Ok(TestCase { input, expected })
    }
} 