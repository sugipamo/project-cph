use std::path::{Path, PathBuf};
use std::os::unix::fs::PermissionsExt;
use std::cell::UnsafeCell;
use nix::unistd::{Uid, Gid};
use tempfile::TempDir;
use super::{BackupManager, FileOperation, FileOperationBuilder, DockerFileOperations, DefaultDockerFileOperations};
use super::error::Result;

/// ファイル操作を管理する構造体
#[derive(Debug)]
pub struct FileManager {
    /// バックアップマネージャー
    backup_manager: BackupManager,
    /// 基準となるパス
    base_path: PathBuf,
    /// 一時ディレクトリ
    temp_dir: UnsafeCell<Option<TempDir>>,
}

impl FileManager {
    /// 新しいファイルマネージャーを作成
    pub fn new() -> Result<Self> {
        Ok(Self {
            backup_manager: BackupManager::new()?,
            base_path: PathBuf::new(),
            temp_dir: UnsafeCell::new(None),
        })
    }

    /// 基準パスを設定
    pub fn with_base_path<P: AsRef<Path>>(mut self, path: P) -> Self {
        self.base_path = path.as_ref().to_path_buf();
        self
    }

    /// トランザクション的なファイル操作を実行
    pub fn execute_operations(&mut self, operations: Vec<Box<dyn FileOperation>>) -> Result<()> {
        // バックアップを作成
        self.backup_manager.create(&self.base_path)?;

        // 操作を実行
        for op in operations {
            if let Err(e) = op.execute() {
                // エラーが発生した場合、バックアップから復元
                self.backup_manager.restore()?;
                return Err(e);
            }
        }

        // 成功した場合、バックアップをクリーンアップ
        self.backup_manager.cleanup()?;
        Ok(())
    }

    /// ディレクトリを作成
    pub fn create_directory(&mut self, path: &Path) -> Result<()> {
        let operations = FileOperationBuilder::new()
            .create_dir(path)
            .build();
        self.execute_operations(operations)
    }

    /// ファイルをコピー
    pub fn copy_file(&mut self, from: &Path, to: &Path) -> Result<()> {
        let operations = FileOperationBuilder::new()
            .copy_file(from, to)
            .build();
        self.execute_operations(operations)
    }

    /// ファイルを移動
    pub fn move_file(&mut self, from: &Path, to: &Path) -> Result<()> {
        let operations = FileOperationBuilder::new()
            .copy_file(from, to)
            .delete_file(from)
            .build();
        self.execute_operations(operations)
    }

    /// ファイルを削除
    pub fn delete_file(&mut self, path: &Path) -> Result<()> {
        let operations = FileOperationBuilder::new()
            .delete_file(path)
            .build();
        self.execute_operations(operations)
    }

    /// バックアップを作成
    pub fn backup(&mut self, path: &Path) -> Result<()> {
        self.backup_manager.create(path)
    }

    /// バックアップから復元
    pub fn rollback(&self) -> Result<()> {
        self.backup_manager.restore()
    }

    /// バックアップをクリーンアップ
    pub fn cleanup(&mut self) -> Result<()> {
        self.backup_manager.cleanup()
    }
}

impl DockerFileOperations for FileManager {
    fn create_temp_directory(&self) -> Result<PathBuf> {
        let temp_dir = TempDir::new()?;
        let temp_path = temp_dir.path().to_path_buf();
        
        // 権限を設定
        self.ensure_directory_permissions(&temp_path)?;

        // 所有者とグループを設定
        let (uid, gid) = self.get_current_user_ids();
        self.set_ownership(&temp_path, Some(uid), Some(gid))?;

        // 一時ディレクトリを保持
        unsafe {
            *self.temp_dir.get() = Some(temp_dir);
        }

        Ok(temp_path)
    }

    fn set_permissions(&self, path: &Path, mode: u32) -> Result<()> {
        let metadata = std::fs::metadata(path)?;
        let mut perms = metadata.permissions();
        perms.set_mode(mode);
        std::fs::set_permissions(path, perms)?;
        Ok(())
    }

    fn set_ownership(&self, path: &Path, uid: Option<Uid>, gid: Option<Gid>) -> Result<()> {
        nix::unistd::chown(path, uid, gid)?;
        Ok(())
    }

    fn write_source_file(&self, dir: &Path, filename: &str, content: &str) -> Result<PathBuf> {
        let file_path = dir.join(filename);
        std::fs::write(&file_path, content)?;

        // 所有者とグループを設定
        let (uid, gid) = self.get_current_user_ids();
        self.set_ownership(&file_path, Some(uid), Some(gid))?;

        Ok(file_path)
    }
}

impl DefaultDockerFileOperations for FileManager {}

impl Drop for FileManager {
    fn drop(&mut self) {
        // 一時ディレクトリを自動的にクリーンアップ
        unsafe {
            if let Some(temp_dir) = (*self.temp_dir.get()).take() {
                let _ = temp_dir.close();
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn test_file_manager() -> Result<()> {
        let mut manager = FileManager::new()?;
        
        // ディレクトリを作成
        let test_dir = PathBuf::from("test_dir");
        manager.create_directory(&test_dir)?;
        assert!(test_dir.exists());

        // ファイルを作成
        let test_file = test_dir.join("test.txt");
        fs::write(&test_file, "test content")?;
        assert!(test_file.exists());

        // ファイルをコピー
        let copy_file = test_dir.join("test_copy.txt");
        manager.copy_file(&test_file, &copy_file)?;
        assert!(copy_file.exists());
        assert_eq!(fs::read_to_string(&copy_file)?, "test content");

        // ファイルを移動
        let move_file = test_dir.join("test_move.txt");
        manager.move_file(&copy_file, &move_file)?;
        assert!(!copy_file.exists());
        assert!(move_file.exists());

        // ファイルを削除
        manager.delete_file(&test_file)?;
        assert!(!test_file.exists());

        // クリーンアップ
        fs::remove_dir_all(test_dir)?;
        Ok(())
    }

    #[test]
    fn test_docker_operations() -> Result<()> {
        let manager = FileManager::new()?;
        
        // 一時ディレクトリの作成
        let temp_dir = manager.create_temp_directory()?;
        assert!(temp_dir.exists());

        // ソースファイルの書き込み
        let file_path = manager.write_source_file(&temp_dir, "test.txt", "test content")?;
        assert!(file_path.exists());
        assert_eq!(fs::read_to_string(&file_path)?, "test content");

        // 権限設定
        manager.set_permissions(&temp_dir, 0o777)?;
        let metadata = fs::metadata(&temp_dir)?;
        assert_eq!(metadata.permissions().mode() & 0o777, 0o777);

        Ok(())
    }
} 