use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tempfile::TempDir;
use anyhow::Result;
use crate::error::fs::io_error as create_io_error;

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
                    .map_err(|e| create_io_error(
                        std::io::Error::new(std::io::ErrorKind::Other, e.to_string()),
                        "バックアップからの復元に失敗しました"
                    ))?;
            }
        }

        Ok(self)
    }

    /// バックアップをクリーンアップし、新しいインスタンスを返す
    pub fn cleanup(self) -> Result<Self> {
        if let Some(backup_dir) = &self.backup_dir {
            if backup_dir.exists() {
                fs::remove_dir_all(&**backup_dir)
                    .map_err(|e| create_io_error(e, "バックアップのクリーンアップに失敗しました"))?;
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

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_backup_lifecycle() -> Result<()> {
        // テスト用の一時ディレクトリを作成
        let temp_dir = tempdir()?;
        let test_file_path = temp_dir.path().join("test.txt");
        std::fs::write(&test_file_path, "test content")?;

        // バックアップの作成
        let manager = BackupManager::new()?;
        let manager = manager.create(temp_dir.path())?;
        
        // バックアップディレクトリが存在することを確認
        assert!(manager.backup_path().is_some());
        assert!(manager.backup_path().unwrap().exists());

        // バックアップから復元
        let manager = manager.restore()?;
        
        // クリーンアップ
        let manager = manager.cleanup()?;
        assert!(manager.backup_path().is_none());

        Ok(())
    }
} 