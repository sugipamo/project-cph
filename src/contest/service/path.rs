use std::path::{Path, PathBuf};
use crate::error::Result;
use crate::contest::error::config_err;

pub struct ContestPath {
    base_dir: PathBuf,
}

impl ContestPath {
    pub fn new<P: AsRef<Path>>(base_dir: P) -> Result<Self> {
        let base_dir = base_dir.as_ref().to_path_buf();
        if !base_dir.exists() {
            return Err(config_err(format!("コンテストディレクトリが存在しません: {:?}", base_dir)));
        }
        Ok(Self { base_dir })
    }

    pub fn get_source_path(&self, problem_id: &str) -> Result<PathBuf> {
        let source_dir = self.base_dir.join("src");
        if !source_dir.exists() {
            return Err(config_err(format!("ソースディレクトリが存在しません: {:?}", source_dir)));
        }

        let source_path = source_dir.join(format!("{}.rs", problem_id));
        if !source_path.exists() {
            return Err(config_err(format!("ソースファイルが存在しません: {:?}", source_path)));
        }

        Ok(source_path)
    }

    pub fn get_test_dir(&self, problem_id: &str) -> Result<PathBuf> {
        let test_dir = self.base_dir.join("test").join(problem_id);
        if !test_dir.exists() {
            return Err(config_err(format!("テストディレクトリが存在しません: {:?}", test_dir)));
        }
        Ok(test_dir)
    }

    pub fn get_build_dir(&self) -> Result<PathBuf> {
        let build_dir = self.base_dir.join("target");
        if !build_dir.exists() {
            std::fs::create_dir_all(&build_dir)
                .map_err(|e| config_err(format!("ビルドディレクトリの作成に失敗しました: {}", e)))?;
        }
        Ok(build_dir)
    }
} 