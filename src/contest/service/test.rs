use std::path::PathBuf;
use crate::contest::error::{ContestError, ContestResult};
use crate::config::Config;

pub struct TestService {
    config: Config,
}

impl TestService {
    pub fn new(config: Config) -> Self {
        Self { config }
    }

    pub fn get_test_dir(&self) -> ContestResult<PathBuf> {
        let test_dir = self.config.get::<String>("system.test.dir")
            .map_err(|e| ContestError::Config(e.to_string()))?;
        
        let path = PathBuf::from(test_dir);
        if !path.exists() {
            std::fs::create_dir_all(&path)
                .map_err(|e| ContestError::Io(e))?;
        }
        Ok(path)
    }

    pub fn get_test_cases(&self, problem_dir: &PathBuf) -> ContestResult<Vec<(PathBuf, PathBuf)>> {
        let mut test_cases = Vec::new();
        let entries = std::fs::read_dir(problem_dir)
            .map_err(|e| ContestError::Io(e))?;

        for entry in entries {
            let entry = entry.map_err(|e| ContestError::Io(e))?;
            let path = entry.path();
            
            if path.is_file() {
                if let Some(file_name) = path.file_name() {
                    let file_name = file_name.to_string_lossy();
                    if file_name.ends_with(".in") {
                        let out_file = path.with_extension("out");
                        if out_file.exists() {
                            test_cases.push((path, out_file));
                        }
                    }
                }
            }
        }

        Ok(test_cases)
    }

    pub fn read_test_case(&self, input_file: &PathBuf, output_file: &PathBuf) -> ContestResult<(String, String)> {
        let input = std::fs::read_to_string(input_file)
            .map_err(|e| ContestError::Io(e))?;
        let expected = std::fs::read_to_string(output_file)
            .map_err(|e| ContestError::Io(e))?;
        
        Ok((input, expected))
    }
} 