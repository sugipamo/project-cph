use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tempfile::TempDir;
use anyhow::{Result, Context};
use crate::error::fs::*;
use crate::fs::ensure_path_exists;

/// バックアップを管理する構造体
#[derive(Debug, Clone)]
pub struct BackupManager {
    /// バックアップディレクトリのパス
    backup_dir: Option<Arc<PathBuf>>,
}

impl BackupManager {
    /// 新しいバックアップマネージャーを作成
    pub fn new() -> Result<Self> {
        Ok(Self {
            backup_dir: None,
        })
    }

    /// バックアップを作成し、新しいインスタンスを返す
    pub fn create<P: AsRef<Path>>(self, target_dir: P) -> Result<Self> {
        if self.backup_dir.is_some() {
            return Ok(self);
        }

        let temp_dir = TempDir::new()
            .context("バックアップディレクトリの作成に失敗しました")?;

        let backup_path = temp_dir.path().to_path_buf();
        ensure_path_exists(&backup_path)?;

        // ターゲットディレクトリの内容をコピー
        if target_dir.as_ref().exists() {
            fs_extra::dir::copy(
                target_dir.as_ref(),
                &backup_path,
                &fs_extra::dir::CopyOptions::new(),
            )
            .map_err(|e| backup_error(format!("バックアップの作成に失敗しました: {}", e)))?;
        }

        Ok(Self {
            backup_dir: Some(Arc::new(backup_path)),
        })
    }

    /// バックアップから復元
    pub fn restore(self) -> Result<Self> {
        if let Some(backup_dir) = &self.backup_dir {
            if backup_dir.exists() {
                let options = fs_extra::dir::CopyOptions::new();
                fs_extra::dir::copy(&**backup_dir, "..", &options)
                    .map_err(|e| backup_error(format!("バックアップからの復元に失敗しました: {}", e)))?;
            }
        }

        Ok(self)
    }

    /// バックアップをクリーンアップし、新しいインスタンスを返す
    pub fn cleanup(self) -> Result<Self> {
        if let Some(backup_dir) = &self.backup_dir {
            if backup_dir.exists() {
                fs::remove_dir_all(&**backup_dir)
                    .context("バックアップのクリーンアップに失敗しました")?;
            }
        }

        Ok(Self {
            backup_dir: None,
        })
    }

    /// バックアップディレクトリのパスを取得
    pub fn backup_path(&self) -> Option<&Path> {
        self.backup_dir.as_ref().map(|p| p.as_path())
    }
} 