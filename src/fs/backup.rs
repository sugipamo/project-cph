use std::path::{Path, PathBuf};
use anyhow::{Result, anyhow};
use chrono::Local;
use tokio::fs;
use crate::message::fs as fs_message;

/// バックアップファイルの管理を行う構造体
#[derive(Debug)]
pub struct Manager {
    /// バックアップディレクトリのパス
    backup_dir: PathBuf,
}

impl Manager {
    /// 新しいバックアップマネージャを作成します
    ///
    /// # Arguments
    /// * `backup_dir` - バックアップディレクトリのパス
    ///
    /// # Returns
    /// * `Result<Self>` - バックアップマネージャのインスタンス
    ///
    /// # Errors
    /// * バックアップディレクトリの作成に失敗した場合
    pub async fn new<P: AsRef<Path> + Send>(backup_dir: P) -> Result<Self> {
        let backup_dir = backup_dir.as_ref().to_path_buf();
        if !backup_dir.exists() {
            fs::create_dir_all(&backup_dir).await
                .map_err(|e| anyhow!(fs_message::error("backup_dir_create_error", e)))?;
        }
        Ok(Self { backup_dir })
    }

    /// ファイルをバックアップします
    ///
    /// # Arguments
    /// * `file_path` - バックアップするファイルのパス
    ///
    /// # Returns
    /// * `Result<()>` - バックアップの結果
    ///
    /// # Errors
    /// * バックアップファイルの作成に失敗した場合
    /// * ファイルのコピーに失敗した場合
    pub async fn backup<P: AsRef<Path> + Send>(&self, file_path: P) -> Result<()> {
        let file_path = file_path.as_ref();
        if !file_path.exists() {
            return Ok(());
        }

        let file_name = file_path.file_name()
            .ok_or_else(|| anyhow!(fs_message::error("filename_get_error", "")))?
            .to_str()
            .ok_or_else(|| anyhow!(fs_message::error("filename_convert_error", "")))?;

        let timestamp = Local::now().format("%Y%m%d_%H%M%S");
        let backup_file_name = format!("{file_name}.{timestamp}.bak");
        let backup_path = self.backup_dir.join(backup_file_name);

        fs::copy(file_path, &backup_path).await
            .map_err(|e| anyhow!(fs_message::error("backup_error", e)))?;

        Ok(())
    }

    /// バックアップファイルを復元します
    ///
    /// # Arguments
    /// * `file_path` - 復元先のファイルパス
    /// * `backup_file_name` - バックアップファイル名
    ///
    /// # Returns
    /// * `Result<()>` - 復元の結果
    ///
    /// # Errors
    /// * バックアップファイルが存在しない場合
    /// * ファイルの復元に失敗した場合
    pub async fn restore<P: AsRef<Path> + Send>(&self, file_path: P, backup_file_name: &str) -> Result<()> {
        let backup_path = self.backup_dir.join(backup_file_name);
        if !backup_path.exists() {
            return Err(anyhow!(fs_message::error("backup_not_found", backup_file_name)));
        }

        fs::copy(&backup_path, file_path.as_ref()).await
            .map_err(|e| anyhow!(fs_message::error("restore_error", e)))?;

        Ok(())
    }

    /// バックアップファイルの一覧を取得します
    ///
    /// # Arguments
    /// * `file_name` - 元のファイル名
    ///
    /// # Returns
    /// * `Result<Vec<String>>` - バックアップファイル名のリスト
    ///
    /// # Errors
    /// * バックアップディレクトリの読み取りに失敗した場合
    pub async fn list_backups(&self, file_name: &str) -> Result<Vec<String>> {
        let mut entries = fs::read_dir(&self.backup_dir).await
            .map_err(|e| anyhow!(fs_message::error("backup_dir_read_error", e)))?;

        let mut backups = Vec::new();
        while let Some(entry) = entries.next_entry().await
            .map_err(|e| anyhow!(fs_message::error("backup_dir_read_error", e)))? {
            if let Some(name) = entry.file_name().to_str() {
                if name.starts_with(file_name) && 
                    std::path::Path::new(name)
                        .extension()
                        .map_or(false, |ext| ext.eq_ignore_ascii_case("bak")) {
                    backups.push(name.to_string());
                }
            }
        }

        Ok(backups)
    }
} 