use std::path::{Path, PathBuf};
use crate::contest::error::{Result, ContestError};
use std::fs;
use super::transaction::FileOperation;

/// ファイルのコピー操作
#[derive(Debug)]
pub struct CopyOperation {
    source: PathBuf,
    destination: PathBuf,
}

impl CopyOperation {
    pub fn new(source: impl AsRef<Path>, destination: impl AsRef<Path>) -> Self {
        Self {
            source: source.as_ref().to_path_buf(),
            destination: destination.as_ref().to_path_buf(),
        }
    }
}

impl FileOperation for CopyOperation {
    fn execute(&self) -> Result<()> {
        fs::copy(&self.source, &self.destination)
            .map_err(|e| ContestError::FileSystem {
                message: "ファイルのコピーに失敗".to_string(),
                source: e,
                path: self.destination.clone(),
            })?;
        Ok(())
    }

    fn rollback(&self) -> Result<()> {
        if self.destination.exists() {
            fs::remove_file(&self.destination)
                .map_err(|e| ContestError::FileSystem {
                    message: "ファイルの削除に失敗".to_string(),
                    source: e,
                    path: self.destination.clone(),
                })?;
        }
        Ok(())
    }

    fn description(&self) -> String {
        format!("Copy {} to {}", self.source.display(), self.destination.display())
    }
}

/// ディレクトリの作成操作
#[derive(Debug)]
pub struct CreateDirOperation {
    path: PathBuf,
}

impl CreateDirOperation {
    pub fn new(path: impl AsRef<Path>) -> Self {
        Self {
            path: path.as_ref().to_path_buf(),
        }
    }
}

impl FileOperation for CreateDirOperation {
    fn execute(&self) -> Result<()> {
        fs::create_dir_all(&self.path)
            .map_err(|e| ContestError::FileSystem {
                message: "ディレクトリの作成に失敗".to_string(),
                source: e,
                path: self.path.clone(),
            })?;
        Ok(())
    }

    fn rollback(&self) -> Result<()> {
        if self.path.exists() {
            fs::remove_dir_all(&self.path)
                .map_err(|e| ContestError::FileSystem {
                    message: "ディレクトリの削除に失敗".to_string(),
                    source: e,
                    path: self.path.clone(),
                })?;
        }
        Ok(())
    }

    fn description(&self) -> String {
        format!("Create directory {}", self.path.display())
    }
}

/// ファイルの削除操作
#[derive(Debug)]
pub struct RemoveOperation {
    path: PathBuf,
    is_dir: bool,
}

impl RemoveOperation {
    pub fn new(path: impl AsRef<Path>, is_dir: bool) -> Self {
        Self {
            path: path.as_ref().to_path_buf(),
            is_dir,
        }
    }
}

impl FileOperation for RemoveOperation {
    fn execute(&self) -> Result<()> {
        if self.is_dir {
            fs::remove_dir_all(&self.path)
        } else {
            fs::remove_file(&self.path)
        }
        .map_err(|e| ContestError::FileSystem {
            message: "ファイル/ディレクトリの削除に失敗".to_string(),
            source: e,
            path: self.path.clone(),
        })?;
        Ok(())
    }

    fn rollback(&self) -> Result<()> {
        // 削除操作のロールバックは、バックアップからの復元に依存
        Ok(())
    }

    fn description(&self) -> String {
        format!("Remove {}", self.path.display())
    }
} 