use std::fs;
use std::path::{Path, PathBuf};
use tempfile::TempDir;
use crate::error::Result;
use super::error::helpers::create_io_error;

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
            .map_err(|e| create_io_error(e, "バックアップディレクトリの作成に失敗しました"))?;

        let backup_path = temp_dir.path().to_path_buf();
        fs::create_dir_all(&backup_path)
            .map_err(|e| create_io_error(e, "バックアップディレクトリの作成に失敗しました"))?;

        // ターゲットディレクトリの内容をコピー
        if target_dir.as_ref().exists() {
            fs_extra::dir::copy(
                target_dir.as_ref(),
                &backup_path,
                &fs_extra::dir::CopyOptions::new(),
            )
            .map_err(|e| create_io_error(
                std::io::Error::new(std::io::ErrorKind::Other, e.to_string()),
                "バックアップの作成に失敗しました"
            ))?;
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
                    .map_err(|e| create_io_error(
                        std::io::Error::new(std::io::ErrorKind::Other, e.to_string()),
                        "バックアップからの復元に失敗しました"
                    ))?;
            }
        }

        Ok(())
    }

    /// バックアップをクリーンアップ
    pub fn cleanup(&mut self) -> Result<()> {
        if let Some(backup_dir) = &self.backup_dir {
            if backup_dir.exists() {
                fs::remove_dir_all(backup_dir)
                    .map_err(|e| create_io_error(e, "バックアップのクリーンアップに失敗しました"))?;
            }
        }

        Ok(())
    }
} 