use std::path::PathBuf;
use crate::contest::error::{ContestError, ContestResult};

pub struct TestCase {
    pub input: String,
    pub expected: String,
}

pub trait TestRunner {
    fn run_test(&self, test_case: &TestCase) -> ContestResult<bool>;
}

pub fn load_test_cases(test_dir: &str) -> ContestResult<Vec<TestCase>> {
    if !std::path::Path::new(test_dir).exists() {
        return Err(ContestError::Config(
            format!("テストディレクトリが存在しません: {}", test_dir)
        ));
    }

    let entries = std::fs::read_dir(test_dir)
        .map_err(|e| ContestError::IO(e))?;

    let mut test_cases = Vec::new();
    for entry in entries {
        let entry = entry.map_err(|e| ContestError::IO(e))?;
        let path = entry.path();

        if path.is_file() && path.extension().map_or(false, |ext| ext == "in") {
            let test_file = path.to_str().ok_or_else(|| ContestError::Config(
                format!("テストファイルのパスが無効です: {:?}", path)
            ))?;

            let expected_path = PathBuf::from(test_file).with_extension("out");
            if !expected_path.exists() {
                return Err(ContestError::Config(
                    format!("期待値ファイルが存在しません: {:?}", expected_path)
                ));
            }

            let input = std::fs::read_to_string(&test_file)
                .map_err(|e| ContestError::IO(e))?;

            let expected = std::fs::read_to_string(&expected_path)
                .map_err(|e| ContestError::IO(e))?;

            test_cases.push(TestCase { input, expected });
        }
    }

    Ok(test_cases)
}

#[cfg(test)]
mod tests {
    // テストの実装
} 