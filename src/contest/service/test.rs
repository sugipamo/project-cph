use std::path::{Path, PathBuf};
use crate::error::Result;
use crate::contest::error::contest_error;
use crate::contest::model::TestCase;

pub struct TestService;

impl TestService {
    pub fn new() -> Self {
        Self
    }

    pub fn read_test_case(&self, input_path: impl AsRef<Path>) -> Result<TestCase> {
        let input_path = input_path.as_ref();
        let expected_path = input_path.with_extension("out");

        let input = std::fs::read_to_string(input_path)
            .map_err(|e| contest_error(
                format!("入力ファイルの読み取りに失敗しました: {:?}, {}", input_path, e)
            ))?;

        let expected = std::fs::read_to_string(&expected_path)
            .map_err(|e| contest_error(
                format!("期待値ファイルの読み取りに失敗しました: {:?}, {}", expected_path, e)
            ))?;

        Ok(TestCase::new(input, expected))
    }

    pub fn find_test_files(&self, test_dir: impl AsRef<Path>) -> Result<Vec<PathBuf>> {
        let test_dir = test_dir.as_ref();
        if !test_dir.exists() {
            return Err(contest_error(
                format!("テストディレクトリが見つかりません: {}", test_dir.display())
            ));
        }

        let entries = std::fs::read_dir(test_dir)
            .map_err(|e| contest_error(
                format!("テストディレクトリの読み取りに失敗しました: {}", e)
            ))?;

        entries
            .filter_map(|entry| {
                entry.ok().and_then(|e| {
                    let path = e.path();
                    if path.is_file() && path.extension().map_or(false, |ext| ext == "in") {
                        let expected_path = path.with_extension("out");
                        if expected_path.exists() {
                            Some(Ok(path))
                        } else {
                            Some(Err(contest_error(
                                format!("期待値ファイルが見つかりません: {:?}", expected_path)
                            )))
                        }
                    } else {
                        None
                    }
                })
            })
            .collect()
    }

    pub fn read_test_cases(&self, test_dir: impl AsRef<Path>) -> Result<Vec<TestCase>> {
        self.find_test_files(test_dir)?
            .into_iter()
            .map(|path| self.read_test_case(&path))
            .collect()
    }
} 