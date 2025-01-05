use std::path::{Path, PathBuf};
use tempfile::TempDir;
use fs_extra::dir::{copy, CopyOptions};
use std::fs;
use crate::contest::error::{Result, ContestError};

/// バックアップを管理する構造体
#[derive(Debug)]
pub struct BackupManager {
    /// バックアップ用の一時ディレクトリ
    backup_dir: Option<TempDir>,
    /// 現在の状態を保持しているパス
    current_state: PathBuf,
}

impl BackupManager {
    /// 新しいバックアップマネージャーを作成
    pub fn new() -> Result<Self> {
        let backup_dir = TempDir::new()
            .map_err(|e| ContestError::FileSystem {
                message: "一時ディレクトリの作成に失敗".to_string(),
                source: std::io::Error::new(std::io::ErrorKind::Other, e.to_string()),
                path: PathBuf::from("temp"),
            })?;

        Ok(Self {
            backup_dir: Some(backup_dir),
            current_state: PathBuf::new(),
        })
    }

    /// バックアップを作成
    pub fn create(&mut self, path: &Path) -> Result<()> {
        if !path.exists() {
            return Ok(());
        }

        let options = CopyOptions::new()
            .overwrite(true)
            .copy_inside(true);

        if let Some(backup_dir) = &self.backup_dir {
            copy(path, backup_dir, &options)
                .map_err(|e| ContestError::Backup {
                    message: "バックアップの作成に失敗".to_string(),
                    path: path.to_path_buf(),
                    source: Some(Box::new(std::io::Error::new(
                        std::io::ErrorKind::Other,
                        e.to_string()
                    ))),
                })?;
        }

        self.current_state = path.to_path_buf();
        Ok(())
    }

    /// バックアップから復元
    pub fn restore(&self) -> Result<()> {
        if !self.current_state.exists() {
            return Ok(());
        }

        // 現在のディレクトリを削除
        if self.current_state.exists() {
            fs::remove_dir_all(&self.current_state)
                .map_err(|e| ContestError::FileSystem {
                    message: "ディレクトリの削除に失敗".to_string(),
                    source: e,
                    path: self.current_state.clone(),
                })?;
        }

        let options = CopyOptions::new()
            .overwrite(true)
            .copy_inside(true);

        if let Some(backup_dir) = &self.backup_dir {
            copy(backup_dir, &self.current_state, &options)
                .map_err(|e| ContestError::Backup {
                    message: "バックアップからの復元に失敗".to_string(),
                    path: self.current_state.clone(),
                    source: Some(Box::new(std::io::Error::new(
                        std::io::ErrorKind::Other,
                        e.to_string()
                    ))),
                })?;
        }

        Ok(())
    }

    /// バックアップを削除
    pub fn cleanup(&mut self) -> Result<()> {
        if let Some(backup_dir) = self.backup_dir.take() {
            let path = backup_dir.path().to_path_buf();
            backup_dir.close()
                .map_err(|e| ContestError::Backup {
                    message: "バックアップの削除に失敗".to_string(),
                    path,
                    source: Some(Box::new(std::io::Error::new(
                        std::io::ErrorKind::Other,
                        e.to_string()
                    ))),
                })?;
        }
        Ok(())
    }

    /// 現在のバックアップパスを取得
    pub fn current_state(&self) -> &Path {
        &self.current_state
    }
} 