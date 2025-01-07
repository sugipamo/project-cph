use std::path::{Path, PathBuf};
use crate::error::Result;
use crate::contest::error::contest_error;

pub struct PathService {
    base_dir: PathBuf,
}

impl PathService {
    pub fn new(base_dir: impl Into<PathBuf>) -> Self {
        Self {
            base_dir: base_dir.into(),
        }
    }

    pub fn validate_base_dir(&self) -> Result<()> {
        if !self.base_dir.exists() {
            return Err(contest_error(
                format!("コンテストディレクトリが存在しません: {:?}", self.base_dir)
            ));
        }
        Ok(())
    }

    pub fn validate_source_dir(&self, source_dir: impl AsRef<Path>) -> Result<()> {
        let source_dir = source_dir.as_ref();
        if !source_dir.exists() {
            return Err(contest_error(
                format!("ソースディレクトリが存在しません: {:?}", source_dir)
            ));
        }
        Ok(())
    }

    pub fn validate_source_file(&self, source_path: impl AsRef<Path>) -> Result<()> {
        let source_path = source_path.as_ref();
        if !source_path.exists() {
            return Err(contest_error(
                format!("ソースファイルが存在しません: {:?}", source_path)
            ));
        }
        Ok(())
    }

    pub fn validate_test_dir(&self, test_dir: impl AsRef<Path>) -> Result<()> {
        let test_dir = test_dir.as_ref();
        if !test_dir.exists() {
            return Err(contest_error(
                format!("テストディレクトリが存在しません: {:?}", test_dir)
            ));
        }
        Ok(())
    }

    pub fn create_build_dir(&self, build_dir: impl AsRef<Path>) -> Result<()> {
        let build_dir = build_dir.as_ref();
        std::fs::create_dir_all(build_dir)
            .map_err(|e| contest_error(
                format!("ビルドディレクトリの作成に失敗しました: {}", e)
            ))?;
        Ok(())
    }

    pub fn get_contest_dir(&self, contest_id: &str) -> Result<PathBuf> {
        let path = self.base_dir.join(contest_id);
        if !path.exists() {
            return Err(contest_error(
                format!("コンテストディレクトリが見つかりません: {}", path.display())
            ));
        }
        Ok(path)
    }

    pub fn get_problem_dir(&self, contest_id: &str, problem_id: &str) -> Result<PathBuf> {
        let path = self.get_contest_dir(contest_id)?.join(problem_id);
        if !path.exists() {
            return Err(contest_error(
                format!("問題ディレクトリが見つかりません: {}", path.display())
            ));
        }
        Ok(path)
    }

    pub fn get_source_file(&self, contest_id: &str, problem_id: &str) -> Result<PathBuf> {
        let path = self.get_problem_dir(contest_id, problem_id)?.join("main.rs");
        if !path.exists() {
            return Err(contest_error(
                format!("ソースファイルが見つかりません: {}", path.display())
            ));
        }
        Ok(path)
    }

    pub fn get_test_dir(&self, contest_id: &str, problem_id: &str) -> Result<PathBuf> {
        let path = self.get_problem_dir(contest_id, problem_id)?.join("test");
        if !path.exists() {
            return Err(contest_error(
                format!("テストディレクトリが見つかりません: {}", path.display())
            ));
        }
        Ok(path)
    }

    pub fn create_contest_dir(&self, contest_id: &str) -> Result<PathBuf> {
        let path = self.base_dir.join(contest_id);
        std::fs::create_dir_all(&path)
            .map_err(|e| contest_error(
                format!("コンテストディレクトリの作成に失敗しました: {}", e)
            ))?;
        Ok(path)
    }
} 