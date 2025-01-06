use std::fs;
use std::path::{Path, PathBuf};
use tempfile::TempDir;
use crate::error::Result;
use super::error::{fs_err, fs_err_with_source};

/// バックアップを管理する構造体
#[derive(Debug)]
pub struct BackupManager {
    /// バックアップディレクトリのパス
    backup_dir: Option<PathBuf>,
}

impl BackupManager {
    /// 新しいバックアップマネージャーを作成
    pub fn new() -> Result<Self> {
        Ok(Self {
            backup_dir: None,
        })
    }

    /// バックアップを作成
    pub fn create<P: AsRef<Path>>(&mut self, target_dir: P) -> Result<()> {
        if self.backup_dir.is_some() {
            return Ok(());
        }

        let temp_dir = TempDir::new()
            .map_err(|e| fs_err_with_source("バックアップディレクトリの作成に失敗しました", e))?;

        let backup_path = temp_dir.path().to_path_buf();
        fs::create_dir_all(&backup_path)
            .map_err(|e| fs_err_with_source("バックアップディレクトリの作成に失敗しました", e))?;

        // ターゲットディレクトリの内容をコピー
        if target_dir.as_ref().exists() {
            fs_extra::dir::copy(
                target_dir.as_ref(),
                &backup_path,
                &fs_extra::dir::CopyOptions::new(),
            )
            .map_err(|e| fs_err(format!("バックアップの作成に失敗しました: {}", e)))?;
        }

        self.backup_dir = Some(backup_path);
        Ok(())
    }

    /// バックアップから復元
    pub fn restore(&self) -> Result<()> {
        if let Some(backup_dir) = &self.backup_dir {
            if backup_dir.exists() {
                let options = fs_extra::dir::CopyOptions::new();
                fs_extra::dir::copy(backup_dir, "..", &options)
                    .map_err(|e| fs_err(format!("バックアップからの復元に失敗しました: {}", e)))?;
            }
        }

        Ok(())
    }

    /// バックアップをクリーンアップ
    pub fn cleanup(&mut self) -> Result<()> {
        if let Some(backup_dir) = &self.backup_dir {
            if backup_dir.exists() {
                fs::remove_dir_all(backup_dir)
                    .map_err(|e| fs_err_with_source("バックアップのクリーンアップに失敗しました", e))?;
            }
        }

        Ok(())
    }
} 