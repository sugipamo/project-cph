use std::path::{Path, PathBuf};
use crate::error::Result;
use super::error::{fs_err, fs_err_with_source};
use super::{FileOperationBuilder, FileTransaction};

pub struct FileManager {
    builder: FileOperationBuilder,
}

impl FileManager {
    pub fn new() -> Result<Self> {
        Ok(Self {
            builder: FileOperationBuilder::new(),
        })
    }

    pub fn create_directory<P: AsRef<Path>>(&self, path: P) -> Result<()> {
        let operation = self.builder.create_dir(path);
        let mut transaction = FileTransaction::new(vec![operation]);
        transaction.execute()
    }

    pub fn copy_file<P: AsRef<Path>>(&self, from: P, to: P) -> Result<()> {
        let operation = self.builder.copy(from, to);
        let mut transaction = FileTransaction::new(vec![operation]);
        transaction.execute()
    }

    pub fn move_file<P: AsRef<Path>>(&self, from: P, to: P) -> Result<()> {
        let copy_operation = self.builder.copy(from.as_ref(), to.as_ref());
        let remove_operation = self.builder.remove(from);
        let mut transaction = FileTransaction::new(vec![copy_operation, remove_operation]);
        transaction.execute()
    }

    pub fn delete_file<P: AsRef<Path>>(&self, path: P) -> Result<()> {
        let operation = self.builder.remove(path);
        let mut transaction = FileTransaction::new(vec![operation]);
        transaction.execute()
    }

    pub fn create_temp_directory(&self) -> Result<PathBuf> {
        let temp_dir = tempfile::TempDir::new()
            .map_err(|e| fs_err_with_source("一時ディレクトリの作成に失敗しました", e))?;
        let path = temp_dir.path().to_path_buf();
        Ok(path)
    }

    pub fn write_source_file<P: AsRef<Path>>(&self, dir: P, filename: &str, content: &str) -> Result<PathBuf> {
        let path = dir.as_ref().join(filename);
        std::fs::write(&path, content)
            .map_err(|e| fs_err_with_source("ソースファイルの書き込みに失敗しました", e))?;
        Ok(path)
    }

    pub fn set_permissions<P: AsRef<Path>>(&self, path: P, mode: u32) -> Result<()> {
        use std::os::unix::fs::PermissionsExt;
        let path = path.as_ref();
        let metadata = std::fs::metadata(path)
            .map_err(|e| fs_err(format!("メタデータの取得に失敗しました: {}", e)))?;
        let mut perms = metadata.permissions();
        perms.set_mode(mode);
        std::fs::set_permissions(path, perms)
            .map_err(|e| fs_err(format!("権限の設定に失敗しました: {}", e)))?;
        Ok(())
    }
} 