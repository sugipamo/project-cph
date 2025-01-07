use std::path::{Path, PathBuf};
use crate::error::Result;
use crate::contest::error::{contest_error, ContestErrorKind};

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
                ContestErrorKind::NotFound,
                format!("コンテストディレクトリが存在しません: {:?}", self.base_dir)
            ));
        }
        Ok(())
    }

    pub fn validate_source_dir(&self, source_dir: impl AsRef<Path>) -> Result<()> {
        let source_dir = source_dir.as_ref();
        if !source_dir.exists() {
            return Err(contest_error(
                ContestErrorKind::NotFound,
                format!("ソースディレクトリが存在しません: {:?}", source_dir)
            ));
        }
        Ok(())
    }

    pub fn validate_source_file(&self, source_path: impl AsRef<Path>) -> Result<()> {
        let source_path = source_path.as_ref();
        if !source_path.exists() {
            return Err(contest_error(
                ContestErrorKind::NotFound,
                format!("ソースファイルが存在しません: {:?}", source_path)
            ));
        }
        Ok(())
    }

    pub fn validate_test_dir(&self, test_dir: impl AsRef<Path>) -> Result<()> {
        let test_dir = test_dir.as_ref();
        if !test_dir.exists() {
            return Err(contest_error(
                ContestErrorKind::NotFound,
                format!("テストディレクトリが存在しません: {:?}", test_dir)
            ));
        }
        Ok(())
    }

    pub fn create_build_dir(&self, build_dir: impl AsRef<Path>) -> Result<()> {
        let build_dir = build_dir.as_ref();
        std::fs::create_dir_all(build_dir)
            .map_err(|e| contest_error(
                ContestErrorKind::Parse,
                format!("ビルドディレクトリの作成に失敗しました: {}", e)
            ))?;
        Ok(())
    }
} 