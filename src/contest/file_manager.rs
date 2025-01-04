use std::path::{Path, PathBuf};
use tempfile::TempDir;
use fs_extra::dir::{copy, CopyOptions};
use std::fs;

type Result<T> = std::result::Result<T, String>;

/// ファイル操作を管理する構造体
/// 
/// この構造体は以下の責務を持ちます：
/// - ファイルのバックアップ作成
/// - エラー時のロールバック
/// - 一時ファイルの管理
pub struct FileManager {
    /// バックアップ用の一時ディレクトリ
    backup_dir: TempDir,
    /// 現在の状態を保持しているパス
    current_state: PathBuf,
}

impl FileManager {
    /// 新しいFileManagerインスタンスを作成
    pub fn new() -> Result<Self> {
        let backup_dir = TempDir::new()
            .map_err(|e| format!("一時ディレクトリの作成に失敗: {}", e))?;
        
        Ok(Self {
            backup_dir,
            current_state: PathBuf::new(),
        })
    }

    /// 指定されたパスのバックアップを作成
    pub fn backup(&mut self, path: &Path) -> Result<()> {
        if !path.exists() {
            return Ok(());
        }

        let options = CopyOptions::new()
            .overwrite(true)
            .copy_inside(true);

        copy(path, &self.backup_dir, &options)
            .map_err(|e| format!("バックアップの作成に失敗: {}", e))?;
        
        self.current_state = path.to_path_buf();
        Ok(())
    }

    /// バックアップから復元
    pub fn rollback(&self) -> Result<()> {
        if !self.current_state.exists() {
            return Ok(());
        }

        // 現在のディレクトリを削除
        if self.current_state.exists() {
            fs::remove_dir_all(&self.current_state)
                .map_err(|e| format!("ディレクトリの削除に失敗: {}", e))?;
        }

        let options = CopyOptions::new()
            .overwrite(true)
            .copy_inside(true);

        copy(&self.backup_dir, &self.current_state, &options)
            .map_err(|e| format!("ロールバックに失敗: {}", e))?;

        Ok(())
    }

    /// バックアップを削除
    pub fn cleanup(&self) -> Result<()> {
        self.backup_dir.close()
            .map_err(|e| format!("一時ディレクトリの削除に失敗: {}", e))?;
        Ok(())
    }

    /// 現在のバックアップパスを取得
    pub fn get_current_state(&self) -> &Path {
        &self.current_state
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn test_backup_and_rollback() -> Result<()> {
        // テスト用の一時ディレクトリを作成
        let test_dir = tempdir().unwrap();
        let test_path = test_dir.path().join("test");
        fs::create_dir(&test_path).unwrap();
        fs::write(test_path.join("test.txt"), "test content").unwrap();

        // FileManagerを作成
        let mut manager = FileManager::new()?;

        // バックアップを作成
        manager.backup(&test_path)?;

        // 元のファイルを変更
        fs::write(test_path.join("test.txt"), "modified content").unwrap();

        // ロールバック
        manager.rollback()?;

        // 内容を確認
        let content = fs::read_to_string(test_path.join("test.txt")).unwrap();
        assert_eq!(content, "test content");

        Ok(())
    }
} 