use std::path::PathBuf;
use crate::error::{CphError, FileSystemError, Result};
use crate::fs::fs_err_with_source;

pub struct Copy {
    from: PathBuf,
    to: PathBuf,
}

impl Copy {
    pub fn new(from: PathBuf, to: PathBuf) -> Self {
        Self { from, to }
    }

    pub fn execute(&self) -> Result<()> {
        if !self.from.exists() {
            return Err(CphError::Fs(FileSystemError::NotFound {
                path: format!("コピー元のファイルが存在しません: {:?}", self.from)
            }));
        }

        if self.from.is_dir() {
            std::fs::create_dir_all(&self.to)
                .map_err(|e| fs_err_with_source("ディレクトリの作成に失敗しました", e))?;

            for entry in std::fs::read_dir(&self.from)
                .map_err(|e| fs_err_with_source("ディレクトリの読み取りに失敗しました", e))? {
                let entry = entry
                    .map_err(|e| fs_err_with_source("ファイルの読み取りに失敗しました", e))?;
                let path = entry.path();
                let new_path = self.to.join(path.file_name().unwrap());
                Copy::new(path, new_path).execute()?;
            }
        } else {
            if let Some(parent) = self.to.parent() {
                std::fs::create_dir_all(parent)
                    .map_err(|e| fs_err_with_source("ディレクトリの作成に失敗しました", e))?;
            }
            std::fs::copy(&self.from, &self.to)
                .map_err(|e| fs_err_with_source("ファイルのコピーに失敗しました", e))?;
        }

        Ok(())
    }

    pub fn rollback(&self) -> Result<()> {
        if self.to.exists() {
            if self.to.is_dir() {
                std::fs::remove_dir_all(&self.to)
                    .map_err(|e| fs_err_with_source("ディレクトリの削除に失敗しました", e))?;
            } else {
                std::fs::remove_file(&self.to)
                    .map_err(|e| fs_err_with_source("ファイルの削除に失敗しました", e))?;
            }
        }
        Ok(())
    }
}

pub struct Remove {
    path: PathBuf,
}

impl Remove {
    pub fn new(path: PathBuf) -> Self {
        Self { path }
    }

    pub fn execute(&self) -> Result<()> {
        if self.path.exists() {
            if self.path.is_dir() {
                std::fs::remove_dir_all(&self.path)
                    .map_err(|e| fs_err_with_source("ディレクトリの削除に失敗しました", e))?;
            } else {
                std::fs::remove_file(&self.path)
                    .map_err(|e| fs_err_with_source("ファイルの削除に失敗しました", e))?;
            }
        }
        Ok(())
    }
}

pub struct Create {
    path: PathBuf,
    is_dir: bool,
}

impl Create {
    pub fn new(path: PathBuf, is_dir: bool) -> Self {
        Self { path, is_dir }
    }

    pub fn execute(&self) -> Result<()> {
        if self.is_dir {
            std::fs::create_dir_all(&self.path)
                .map_err(|e| fs_err_with_source("ディレクトリの作成に失敗しました", e))?;
        } else {
            if let Some(parent) = self.path.parent() {
                std::fs::create_dir_all(parent)
                    .map_err(|e| fs_err_with_source("ディレクトリの作成に失敗しました", e))?;
            }
            std::fs::File::create(&self.path)
                .map_err(|e| fs_err_with_source("ファイルの作成に失敗しました", e))?;
        }
        Ok(())
    }
} 