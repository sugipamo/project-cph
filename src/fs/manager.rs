use std::path::{Path, PathBuf};
use std::sync::Arc;
use crate::error::Result;
use crate::fs::error::{io_err, not_found_err, invalid_path_err};
use crate::fs::transaction::{FileTransaction, FileOperation, CreateFileOperation, DeleteFileOperation};

#[derive(Debug, Clone)]
pub struct FileManager {
    root: Arc<PathBuf>,
    transaction: Option<FileTransaction>,
}

impl FileManager {
    pub fn new(root: impl Into<PathBuf>) -> Self {
        Self {
            root: Arc::new(root.into()),
            transaction: None,
        }
    }

    pub fn begin_transaction(self) -> Self {
        Self {
            root: self.root.clone(),
            transaction: Some(FileTransaction::new()),
        }
    }

    pub fn commit(self) -> Result<Self> {
        match self.transaction {
            Some(transaction) => {
                let _executed = transaction.execute()?;
                Ok(Self {
                    root: self.root,
                    transaction: None,
                })
            }
            None => Ok(self),
        }
    }

    pub fn rollback(self) -> Self {
        match self.transaction {
            Some(_) => Self {
                root: self.root,
                transaction: None,
            },
            None => self,
        }
    }

    // パスの正規化と検証を行うヘルパーメソッド
    fn normalize_path(&self, path: impl AsRef<Path>) -> Result<PathBuf> {
        let path = path.as_ref();
        
        // 絶対パスの場合はエラー
        if path.is_absolute() {
            return Err(invalid_path_err(format!(
                "絶対パスは使用できません: {}",
                path.display()
            )));
        }

        // パスのトラバーサルを防ぐ
        let normalized = path.components()
            .fold(Ok(PathBuf::new()), |acc, component| {
                let mut path = acc?;
                match component {
                    std::path::Component::ParentDir => {
                        if path.pop() {
                            Ok(path)
                        } else {
                            Err(invalid_path_err(format!(
                                "パスが親ディレクトリを超えて遡ることはできません: {}",
                                path.display()
                            )))
                        }
                    },
                    std::path::Component::Normal(name) => {
                        path.push(name);
                        Ok(path)
                    },
                    _ => Ok(path),
                }
            })?;

        Ok(self.root.join(normalized))
    }

    pub fn read_file(&self, path: impl AsRef<Path>) -> Result<String> {
        let path = self.normalize_path(path)?;
        if !path.exists() {
            return Err(not_found_err(format!(
                "ファイルが見つかりません: {}",
                path.display()
            )));
        }
        std::fs::read_to_string(&path)
            .map_err(|e| io_err(e, format!("ファイルの読み込みに失敗: {}", path.display())))
    }

    pub fn write_file(self, path: impl AsRef<Path>, content: impl AsRef<str>) -> Result<Self> {
        let path = self.normalize_path(path)?;
        match &self.transaction {
            Some(transaction) => {
                let operation = Arc::new(CreateFileOperation::new(path, content.as_ref().to_string()));
                Ok(Self {
                    root: self.root,
                    transaction: Some(transaction.clone().with_operation(operation)),
                })
            }
            None => {
                let mut transaction = FileTransaction::new();
                let operation = Arc::new(CreateFileOperation::new(path, content.as_ref().to_string()));
                transaction = transaction.with_operation(operation);
                let _executed = transaction.execute()?;
                Ok(Self {
                    root: self.root,
                    transaction: None,
                })
            }
        }
    }

    pub fn delete_file(self, path: impl AsRef<Path>) -> Result<Self> {
        let path = self.normalize_path(path)?;
        match &self.transaction {
            Some(transaction) => {
                let operation = Arc::new(DeleteFileOperation::new(path)?);
                Ok(Self {
                    root: self.root,
                    transaction: Some(transaction.clone().with_operation(operation)),
                })
            }
            None => {
                let mut transaction = FileTransaction::new();
                let operation = Arc::new(DeleteFileOperation::new(path)?);
                transaction = transaction.with_operation(operation);
                let _executed = transaction.execute()?;
                Ok(Self {
                    root: self.root,
                    transaction: None,
                })
            }
        }
    }

    pub fn create_dir(self, path: impl AsRef<Path>) -> Result<Self> {
        let path = self.normalize_path(path)?;
        match &self.transaction {
            Some(transaction) => {
                let operation = Arc::new(CreateFileOperation::new(path, String::new()));
                Ok(Self {
                    root: self.root,
                    transaction: Some(transaction.clone().with_operation(operation)),
                })
            }
            None => {
                std::fs::create_dir_all(&path)
                    .map_err(|e| io_err(e, format!("ディレクトリの作成に失敗: {}", path.display())))?;
                Ok(self)
            }
        }
    }

    pub fn exists(&self, path: impl AsRef<Path>) -> Result<bool> {
        let path = self.normalize_path(path)?;
        Ok(path.exists())
    }

    pub fn root_path(&self) -> &Path {
        self.root.as_ref()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_transaction_operations() -> Result<()> {
        let temp_dir = tempdir().unwrap();
        let manager = FileManager::new(temp_dir.path().to_string_lossy().to_string());

        // トランザクション内での操作
        let manager = manager.begin_transaction()
            .write_file("test1.txt", "Hello")?
            .write_file("test2.txt", "World")?
            .commit()?;

        // ファイルの確認
        assert_eq!(manager.read_file("test1.txt")?, "Hello");
        assert_eq!(manager.read_file("test2.txt")?, "World");

        // ロールバックのテスト
        let manager = manager.begin_transaction()
            .write_file("test3.txt", "Should not exist")?
            .rollback();

        assert!(manager.read_file("test3.txt").is_err());

        Ok(())
    }

    // ... 既存のテストは残す ...
} 