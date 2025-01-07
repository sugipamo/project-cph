use std::path::{Path, PathBuf};
use std::sync::Arc;
use crate::error::Result;
use crate::fs::error::helpers::{create_io_error, create_not_found_error, create_invalid_path_error};
use crate::fs::transaction::{FileTransaction, FileOperation, CreateFileOperation, DeleteFileOperation};

// ファイルマネージャーの状態を表現する型
#[derive(Debug, Clone)]
pub enum ManagerState {
    Idle,
    InTransaction(FileTransaction),
}

// 状態遷移を表現する型
#[derive(Debug, Clone)]
pub enum ManagerTransition {
    BeginTransaction,
    AddOperation(Arc<dyn FileOperation>),
    Commit,
    Rollback,
}

#[derive(Debug, Clone)]
pub struct FileManager {
    root: Arc<PathBuf>,
    state: ManagerState,
}

impl FileManager {
    pub fn new(root: impl Into<PathBuf>) -> Self {
        Self {
            root: Arc::new(root.into()),
            state: ManagerState::Idle,
        }
    }

    // 状態遷移を適用するメソッド
    fn apply_transition(self, transition: ManagerTransition) -> Result<Self> {
        match (self.state, transition) {
            (ManagerState::Idle, ManagerTransition::BeginTransaction) => {
                Ok(Self {
                    root: self.root,
                    state: ManagerState::InTransaction(FileTransaction::new()),
                })
            },
            (ManagerState::InTransaction(transaction), ManagerTransition::AddOperation(operation)) => {
                let new_transaction = transaction.with_operation(operation)?;
                Ok(Self {
                    root: self.root,
                    state: ManagerState::InTransaction(new_transaction),
                })
            },
            (ManagerState::InTransaction(transaction), ManagerTransition::Commit) => {
                let _ = transaction.execute()?;
                Ok(Self {
                    root: self.root,
                    state: ManagerState::Idle,
                })
            },
            (ManagerState::InTransaction(_), ManagerTransition::Rollback) => {
                Ok(Self {
                    root: self.root,
                    state: ManagerState::Idle,
                })
            },
            (state, transition) => {
                Err(create_io_error(
                    std::io::Error::new(
                        std::io::ErrorKind::InvalidInput,
                        format!("無効な状態遷移: {:?} -> {:?}", state, transition)
                    ),
                    "ファイルマネージャー状態遷移エラー"
                ))
            }
        }
    }

    // パスの正規化と検証を行うヘルパーメソッド
    fn normalize_path(&self, path: impl AsRef<Path>) -> Result<PathBuf> {
        let path = path.as_ref();
        
        // 絶対パスの場合はエラー
        if path.is_absolute() {
            return Err(create_invalid_path_error(path));
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
                            Err(create_invalid_path_error(path))
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

    // 公開APIメソッド
    pub fn begin_transaction(self) -> Result<Self> {
        self.apply_transition(ManagerTransition::BeginTransaction)
    }

    pub fn commit(self) -> Result<Self> {
        self.apply_transition(ManagerTransition::Commit)
    }

    pub fn rollback(self) -> Result<Self> {
        self.apply_transition(ManagerTransition::Rollback)
    }

    pub fn read_file(&self, path: impl AsRef<Path>) -> Result<String> {
        let path = self.normalize_path(path)?;
        if !path.exists() {
            return Err(create_not_found_error(&path));
        }
        std::fs::read_to_string(&path)
            .map_err(|e| create_io_error(e, format!("ファイルの読み込みに失敗: {}", path.display())))
    }

    pub fn write_file(self, path: impl AsRef<Path>, content: impl AsRef<str>) -> Result<Self> {
        let path = self.normalize_path(path)?;
        let operation = Arc::new(CreateFileOperation::new(path, content.as_ref().to_string()));
        
        match self.state {
            ManagerState::InTransaction(_) => {
                self.apply_transition(ManagerTransition::AddOperation(operation))
            },
            ManagerState::Idle => {
                self.begin_transaction()?
                    .apply_transition(ManagerTransition::AddOperation(operation))?
                    .commit()
            }
        }
    }

    pub fn delete_file(self, path: impl AsRef<Path>) -> Result<Self> {
        let path = self.normalize_path(path)?;
        let operation = Arc::new(DeleteFileOperation::new(path)?);
        
        match self.state {
            ManagerState::InTransaction(_) => {
                self.apply_transition(ManagerTransition::AddOperation(operation))
            },
            ManagerState::Idle => {
                self.begin_transaction()?
                    .apply_transition(ManagerTransition::AddOperation(operation))?
                    .commit()
            }
        }
    }

    pub fn create_dir(self, path: impl AsRef<Path>) -> Result<Self> {
        let path = self.normalize_path(path)?;
        match self.state {
            ManagerState::InTransaction(_) => {
                let operation = Arc::new(CreateFileOperation::new(path, String::new()));
                self.apply_transition(ManagerTransition::AddOperation(operation))
            },
            ManagerState::Idle => {
                std::fs::create_dir_all(&path)
                    .map_err(|e| create_io_error(e, format!("ディレクトリの作成に失敗: {}", path.display())))?;
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
        let manager = manager.begin_transaction()?
            .write_file("test1.txt", "Hello")?
            .write_file("test2.txt", "World")?
            .commit()?;

        // ファイルの確認
        assert_eq!(manager.read_file("test1.txt")?, "Hello");
        assert_eq!(manager.read_file("test2.txt")?, "World");

        // ロールバックのテスト
        let manager = manager.begin_transaction()?
            .write_file("test3.txt", "Should not exist")?
            .rollback()?;

        assert!(manager.read_file("test3.txt").is_err());

        Ok(())
    }
} 