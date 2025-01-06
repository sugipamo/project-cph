use std::path::PathBuf;
use crate::config::Config;
use crate::contest::error::{ContestResult, ContestError};
use crate::test::TestCase;

pub struct TestService {
    config: Config,
}

impl TestService {
    pub fn new(config: Config) -> Self {
        Self { config }
    }

    pub async fn run_tests(&self, problem_id: &str) -> ContestResult<()> {
        let test_dir = self.get_test_dir(problem_id)?;
        if !test_dir.exists() {
            return Err(ContestError::Config(
                format!("テストディレクトリが存在しません: {:?}", test_dir)
            ));
        }

        let entries = std::fs::read_dir(&test_dir)
            .map_err(|e| ContestError::IO(e))?;

        for entry in entries {
            let entry = entry.map_err(|e| ContestError::IO(e))?;
            let path = entry.path();
            if path.is_file() && path.extension().map_or(false, |ext| ext == "in") {
                let _test_case = self.load_test_case(&path)?;
                // TODO: テストケースの実行処理を実装
            }
        }

        Ok(())
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