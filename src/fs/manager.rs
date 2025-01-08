use std::path::{Path, PathBuf};
use std::sync::Arc;
use anyhow::{Result, Context};
use crate::error::fs::*;
use crate::fs::path::normalize_path;
use crate::fs::{FileOperation, FileTransaction, CreateFileOperation, DeleteFileOperation};

// ファイルマネジャーの状態を表現する型
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
                Err(transaction_error(format!("無効な状態遷移: {:?} -> {:?}", state, transition)))
            }
        }
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
        let path = normalize_path(&*self.root, path)?;
        if !path.exists() {
            return Err(not_found_error(&path));
        }
        std::fs::read_to_string(&path)
            .context(format!("ファイルの読み込みに失敗: {}", path.display()))
    }

    pub fn write_file(self, path: impl AsRef<Path>, content: impl AsRef<str>) -> Result<Self> {
        let path = normalize_path(&*self.root, path)?;
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
        let path = normalize_path(&*self.root, path)?;
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
        let path = normalize_path(&*self.root, path)?;
        match self.state {
            ManagerState::InTransaction(_) => {
                let operation = Arc::new(CreateFileOperation::new(path, String::new()));
                self.apply_transition(ManagerTransition::AddOperation(operation))
            },
            ManagerState::Idle => {
                std::fs::create_dir_all(&path)
                    .context(format!("ディレクトリの作成に失敗: {}", path.display()))?;
                Ok(self)
            }
        }
    }

    pub fn exists(&self, path: impl AsRef<Path>) -> Result<bool> {
        let path = normalize_path(&*self.root, path)?;
        Ok(path.exists())
    }

    pub fn root_path(&self) -> &Path {
        self.root.as_ref()
    }
} 