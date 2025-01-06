use std::fs;
use std::path::{Path, PathBuf};
use fs_extra::dir::{self, CopyOptions};
use super::error::{Result, FsError};

/// バックアップを管理する構造体
#[derive(Debug)]
pub struct BackupManager {
    /// バックアップディレクトリのパス
    backup_dir: Option<PathBuf>,
}

impl BackupManager {
    /// 新しいバックアップマネージャーを作成
    pub fn new() -> Result<Self> {
        let backup_dir = std::env::temp_dir().join("cph_backup");
        fs::create_dir_all(&backup_dir)
            .map_err(|e| FsError::FileSystem {
                message: format!("バックアップディレクトリの作成に失敗しました: {}", e),
                source: Some(e),
            })?;

        Ok(Self {
            backup_dir: Some(backup_dir),
        })
    }

    /// バックアップを作成
    pub fn create(&mut self, path: &Path) -> Result<()> {
        if let Some(backup_dir) = &self.backup_dir {
            // 既存のバックアップをクリーンアップ
            if backup_dir.exists() {
                fs::remove_dir_all(backup_dir)
                    .map_err(|e| FsError::Backup {
                        message: format!("既存のバックアップの削除に失敗しました: {}", e),
                        source: Some(e),
                    })?;
            }

            // バックアップディレクトリを作成
            fs::create_dir_all(backup_dir)
                .map_err(|e| FsError::Backup {
                        message: format!("バックアップディレクトリの作成に失敗しました: {}", e),
                        source: Some(e),
                    })?;

            // ディレクトリをコピー
            let options = CopyOptions::new();
            dir::copy(path, backup_dir, &options)
                .map_err(|e| FsError::FileSystem {
                    message: format!("ファイルのバックアップに失敗しました: {}", e),
                    source: Some(std::io::Error::new(std::io::ErrorKind::Other, e.to_string())),
                })?;
        }

        Ok(())
    }

    /// バックアップから復元
    pub fn restore(&self) -> Result<()> {
        if let Some(backup_dir) = &self.backup_dir {
            if backup_dir.exists() {
                let options = CopyOptions::new();
                dir::copy(backup_dir, "..", &options)
                    .map_err(|e| FsError::Backup {
                        message: format!("バックアップからの復元に失敗しました: {}", e),
                        source: Some(std::io::Error::new(std::io::ErrorKind::Other, e.to_string())),
                    })?;
            }
        }

        Ok(())
    }

    /// バックアップをクリーンアップ
    pub fn cleanup(&mut self) -> Result<()> {
        if let Some(backup_dir) = &self.backup_dir {
            if backup_dir.exists() {
                fs::remove_dir_all(backup_dir)
                    .map_err(|e| FsError::Backup {
                        message: format!("バックアップのクリーンアップに失敗しました: {}", e),
                        source: Some(e),
                    })?;
            }
        }

        Ok(())
    }
} 