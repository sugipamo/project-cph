use std::path::{Path, PathBuf};
use anyhow::{Result, anyhow};
use crate::message::contest;

pub struct Service {
    base_dir: PathBuf,
}

impl Service {
    #[must_use = "この関数は新しいPathServiceインスタンスを返します"]
    pub fn new(base_dir: impl Into<PathBuf>) -> Self {
        Self {
            base_dir: base_dir.into(),
        }
    }

    ///ベースディレクトリの存在を確認します。
    /// 
    /// # Errors
    /// - ベースディレクトリが存在しない場合
    pub fn validate_base_dir(&self) -> Result<()> {
        if !self.base_dir.exists() {
            return Err(anyhow!(contest::error("contest_dir_not_found", self.base_dir.display())));
        }
        Ok(())
    }

    /// ソースディレクトリの存在を確認します。
    /// 
    /// # Errors
    /// - ソースディレクトリが存在しない場合
    pub fn validate_source_dir(&self, source_dir: impl AsRef<Path>) -> Result<()> {
        let source_dir = source_dir.as_ref();
        if !source_dir.exists() {
            return Err(anyhow!(contest::error("source_dir_not_found", source_dir.display())));
        }
        Ok(())
    }

    /// ソース�ァイルの存在を確認します。
    /// 
    /// # Errors
    /// - ソースファイルが存在しない場合
    pub fn validate_source_file(&self, source_path: impl AsRef<Path>) -> Result<()> {
        let source_path = source_path.as_ref();
        if !source_path.exists() {
            return Err(anyhow!(
                "ソースファイルが存在しません: {:?}", source_path
            ));
        }
        Ok(())
    }

    /// テストディレクトリの存在を確認します。
    /// 
    /// # Errors
    /// - テストディレクトリが存在しない場合
    pub fn validate_test_dir(&self, test_dir: impl AsRef<Path>) -> Result<()> {
        let test_dir = test_dir.as_ref();
        if !test_dir.exists() {
            return Err(anyhow!(
                "テストディレクトリが存在しません: {:?}", test_dir
            ));
        }
        Ok(())
    }

    /// ビルドディレクトリを作成します。
    /// 
    /// # Errors
    /// - ディレクトリの作成に失敗した場合
    pub fn create_build_dir(&self, build_dir: impl AsRef<Path>) -> Result<()> {
        let build_dir = build_dir.as_ref();
        std::fs::create_dir_all(build_dir)
            .map_err(|e| anyhow!(
                "ビルドディレクトリの作成に失敗しました: {}", e
            ))?;
        Ok(())
    }

    /// コンテストディレクトリのパスを取得します。
    /// 
    /// # Errors
    /// - コンテストディレクトリが存在しない場合
    pub fn get_contest_dir(&self, contest_id: &str) -> Result<PathBuf> {
        let path = self.base_dir.join(contest_id);
        if !path.exists() {
            return Err(anyhow!(
                "コンテストディレクトリが見つかりません: {}", path.display()
            ));
        }
        Ok(path)
    }

    /// 問題ディレクトリのパスを取得します。
    /// 
    /// # Errors
    /// - コンテストディレクトリが存在しない場合
    /// - 問題ディレクトリが存在しない場合
    pub fn get_problem_dir(&self, contest_id: &str, problem_id: &str) -> Result<PathBuf> {
        let path = self.get_contest_dir(contest_id)?.join(problem_id);
        if !path.exists() {
            return Err(anyhow!(
                "問題ディレクトリが見つかりません: {}", path.display()
            ));
        }
        Ok(path)
    }

    /// ソースファイルのパスを取得します。
    /// 
    /// # Errors
    /// - コンテストディレクトリが存在しない場合
    /// - 問題ディレクトリが存在しない場合
    /// - ソースファイルが存在しない場合
    pub fn get_source_file(&self, contest_id: &str, problem_id: &str) -> Result<PathBuf> {
        let path = self.get_problem_dir(contest_id, problem_id)?.join("main.rs");
        if !path.exists() {
            return Err(anyhow!(
                "ソースファイルが見つかりません: {}", path.display()
            ));
        }
        Ok(path)
    }

    /// テストディレクトリのパスを取得します。
    /// 
    /// # Errors
    /// - コンテストディレクトリが存在しない場合
    /// - 問題ディレクトリが存在しない場合
    /// - テストディレクトリが存在しない場合
    pub fn get_test_dir(&self, contest_id: &str, problem_id: &str) -> Result<PathBuf> {
        let path = self.get_problem_dir(contest_id, problem_id)?.join("test");
        if !path.exists() {
            return Err(anyhow!(
                "テストディレクトリが見つかりません: {}", path.display()
            ));
        }
        Ok(path)
    }

    /// コンテストディレクトリを作成します。
    /// 
    /// # Errors
    /// - ディレクトリの作成に失敗した場合
    pub fn create_contest_dir(&self, contest_id: &str) -> Result<PathBuf> {
        let path = self.base_dir.join(contest_id);
        std::fs::create_dir_all(&path)
            .map_err(|e| anyhow!(
                "コンテストディレクトリの作成に失敗しました: {}", e
            ))?;
        Ok(path)
    }
}