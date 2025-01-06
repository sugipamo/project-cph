use std::path::{Path, PathBuf};
use crate::error::Result;
use super::error::{fs_err, fs_err_with_source};
use super::transaction::FileOperation;

pub struct FileOperationBuilder;

impl FileOperationBuilder {
    pub fn new() -> Self {
        Self
    }

    pub fn create_dir<P: AsRef<Path>>(&self, path: P) -> Box<dyn FileOperation> {
        Box::new(CreateDirOperation {
            path: path.as_ref().to_path_buf(),
        })
    }

    pub fn copy<P: AsRef<Path>>(&self, from: P, to: P) -> Box<dyn FileOperation> {
        Box::new(CopyOperation {
            from: from.as_ref().to_path_buf(),
            to: to.as_ref().to_path_buf(),
        })
    }

    pub fn remove<P: AsRef<Path>>(&self, path: P) -> Box<dyn FileOperation> {
        Box::new(RemoveOperation {
            path: path.as_ref().to_path_buf(),
        })
    }
}

#[derive(Debug)]
pub struct CreateDirOperation {
    path: PathBuf,
}

impl FileOperation for CreateDirOperation {
    fn execute(&self) -> Result<()> {
        std::fs::create_dir_all(&self.path)
            .map_err(|e| fs_err_with_source("ディレクトリの作成に失敗しました", e))
    }

    fn rollback(&self) -> Result<()> {
        if self.path.exists() {
            std::fs::remove_dir_all(&self.path)
                .map_err(|e| fs_err_with_source("ディレクトリの削除に失敗しました", e))
        } else {
            Ok(())
        }
    }
}

#[derive(Debug)]
pub struct CopyOperation {
    from: PathBuf,
    to: PathBuf,
}

impl FileOperation for CopyOperation {
    fn execute(&self) -> Result<()> {
        if !self.from.exists() {
            return Err(fs_err(format!(
                "コピー元のファイルが存在しません: {:?}",
                self.from
            )));
        }

        if self.from.is_dir() {
            fs_extra::dir::copy(
                &self.from,
                &self.to,
                &fs_extra::dir::CopyOptions::new(),
            )
            .map_err(|e| fs_err(format!("ディレクトリのコピーに失敗しました: {}", e)))?;
        } else {
            fs_extra::file::copy(
                &self.from,
                &self.to,
                &fs_extra::file::CopyOptions::new(),
            )
            .map_err(|e| fs_err(format!("ファイルのコピーに失敗しました: {}", e)))?;
        }

        Ok(())
    }

    fn rollback(&self) -> Result<()> {
        if self.to.exists() {
            if self.to.is_dir() {
                std::fs::remove_dir_all(&self.to)
                    .map_err(|e| fs_err_with_source("ディレクトリの削除に失敗しました", e))
            } else {
                std::fs::remove_file(&self.to)
                    .map_err(|e| fs_err_with_source("ファイルの削除に失敗しました", e))
            }
        } else {
            Ok(())
        }
    }
}

#[derive(Debug)]
pub struct RemoveOperation {
    path: PathBuf,
}

impl FileOperation for RemoveOperation {
    fn execute(&self) -> Result<()> {
        if self.path.exists() {
            if self.path.is_dir() {
                std::fs::remove_dir_all(&self.path)
                    .map_err(|e| fs_err_with_source("ディレクトリの削除に失敗しました", e))
            } else {
                std::fs::remove_file(&self.path)
                    .map_err(|e| fs_err_with_source("ファイルの削除に失敗しました", e))
            }
        } else {
            Ok(())
        }
    }

    fn rollback(&self) -> Result<()> {
        // 削除操作のロールバックは、ファイルの復元が必要
        // ここでは単純な実装として、空のファイルを作成
        if !self.path.exists() {
            if let Some(parent) = self.path.parent() {
                std::fs::create_dir_all(parent)
                    .map_err(|e| fs_err_with_source("親ディレクトリの作成に失敗しました", e))?;
            }
            std::fs::File::create(&self.path)
                .map_err(|e| fs_err_with_source("ファイルの作成に失敗しました", e))?;
        }
        Ok(())
    }
} 