use std::path::PathBuf;
use crate::error::Result;
use crate::contest::error::config_err;

pub struct TestService {
    test_dir: PathBuf,
}

impl TestService {
    pub fn new(test_dir: PathBuf) -> Self {
        Self { test_dir }
    }

    pub fn add_test_case(&self, input: &str, expected: &str) -> Result<()> {
        if input.is_empty() {
            return Err(config_err("入力が空です".to_string()));
        }
        if expected.is_empty() {
            return Err(config_err("期待値が空です".to_string()));
        }

        let test_count = self.get_test_count()?;
        let input_file = self.test_dir.join(format!("test{}.in", test_count + 1));
        let expected_file = self.test_dir.join(format!("test{}.out", test_count + 1));

        std::fs::write(&input_file, input)
            .map_err(|e| config_err(format!("テストケースの入力ファイルの作成に失敗しました: {}", e)))?;
        std::fs::write(&expected_file, expected)
            .map_err(|e| config_err(format!("テストケースの期待値ファイルの作成に失敗しました: {}", e)))?;

        Ok(())
    }

    pub fn get_test_count(&self) -> Result<usize> {
        let entries = std::fs::read_dir(&self.test_dir)
            .map_err(|e| config_err(format!("テストディレクトリの読み取りに失敗しました: {}", e)))?;

        let count = entries
            .filter_map(|entry| entry.ok())
            .filter(|entry| {
                entry.path()
                    .extension()
                    .map(|ext| ext == "in")
                    .unwrap_or(false)
            })
            .count();

        Ok(count)
    }

    pub fn get_test_cases(&self) -> Result<Vec<(String, String)>> {
        let mut test_cases = Vec::new();
        let test_count = self.get_test_count()?;

        for i in 1..=test_count {
            let input_file = self.test_dir.join(format!("test{}.in", i));
            let expected_file = self.test_dir.join(format!("test{}.out", i));

            let input = std::fs::read_to_string(&input_file)
                .map_err(|e| config_err(format!("テストケースの入力ファイルの読み取りに失敗しました: {}", e)))?;
            let expected = std::fs::read_to_string(&expected_file)
                .map_err(|e| config_err(format!("テストケースの期待値ファイルの読み取りに失敗しました: {}", e)))?;

            test_cases.push((input, expected));
        }

        Ok(test_cases)
    }
} 