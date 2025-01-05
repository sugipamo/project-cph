use std::path::{Path, PathBuf};
use super::{BackupManager, FileOperation, FileOperationBuilder};
use crate::contest::error::Result;

/// ファイル操作を管理する構造体
#[derive(Debug)]
pub struct FileManager {
    /// バックアップマネージャー
    backup_manager: BackupManager,
    /// 基準となるパス
    base_path: PathBuf,
}

impl FileManager {
    /// 新しいファイルマネージャーを作成
    pub fn new() -> Result<Self> {
        Ok(Self {
            backup_manager: BackupManager::new()?,
            base_path: PathBuf::new(),
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
            .move_file(from, to)
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