use std::path::{Path, PathBuf};
use std::sync::Arc;
use anyhow::Result;
use crate::fs::path::normalize_path;
use crate::fs::{FileOperation, Transaction, CreateFileOperation, DeleteFileOperation};
use crate::fs_err;

/// ファイル管理の状態を表現する型
#[derive(Debug, Clone)]
pub enum State {
    Idle,
    InTransaction(Transaction),
}

/// 状態遷移を表現する型
#[derive(Debug, Clone)]
pub enum Transition {
    BeginTransaction,
    AddOperation(Arc<dyn FileOperation>),
    Commit,
    Rollback,
}

/// ファイル管理を行う構造体
#[derive(Debug, Clone)]
pub struct Manager {
    root: Arc<PathBuf>,
    state: State,
}

impl Manager {
    pub fn new(root: impl Into<PathBuf>) -> Self {
        Self {
            root: Arc::new(root.into()),
            state: State::Idle,
        }
    }

    // 状態遷移を適用するメソッド
    fn apply_transition(self, transition: Transition) -> Result<Self> {
        match (self.state, transition) {
            (State::Idle, Transition::BeginTransaction) => {
                Ok(Self {
                    root: self.root,
                    state: State::InTransaction(Transaction::new()),
                })
            },
            (State::InTransaction(transaction), Transition::AddOperation(operation)) => {
                let new_transaction = transaction.with_operation(operation)?;
                Ok(Self {
                    root: self.root,
                    state: State::InTransaction(new_transaction),
                })
            },
            (State::InTransaction(transaction), Transition::Commit) => {
                let _ = transaction.execute()?;
                Ok(Self {
                    root: self.root,
                    state: State::Idle,
                })
            },
            (State::InTransaction(_), Transition::Rollback) => {
                Ok(Self {
                    root: self.root,
                    state: State::Idle,
                })
            },
            (state, transition) => {
                Err(fs_err!("無効な状態遷移: {:?} -> {:?}", state, transition))
            }
        }
    }

    // 公開APIメソッド
    pub fn begin_transaction(self) -> Result<Self> {
        self.apply_transition(Transition::BeginTransaction)
    }

    pub fn commit(self) -> Result<Self> {
        self.apply_transition(Transition::Commit)
    }

    pub fn rollback(self) -> Result<Self> {
        self.apply_transition(Transition::Rollback)
    }

    pub fn read_file(&self, path: impl AsRef<Path>) -> Result<String> {
        let path = normalize_path(&*self.root, path)?;
        if !path.exists() {
            return Err(fs_err!("ファイルが見つかりません: {}", path.display()));
        }
        std::fs::read_to_string(&path)
            .map_err(|e| fs_err!("ファイルの読み込みに失敗: {}: {}", path.display(), e))
    }

    pub fn write_file(self, path: impl AsRef<Path>, content: impl AsRef<str>) -> Result<Self> {
        let path = normalize_path(&*self.root, path)?;
        let operation = Arc::new(CreateFileOperation::new(path, content.as_ref().to_string()));
        
        match self.state {
            State::InTransaction(_) => {
                self.apply_transition(Transition::AddOperation(operation))
            },
            State::Idle => {
                self.begin_transaction()?
                    .apply_transition(Transition::AddOperation(operation))?
                    .commit()
            }
        }
    }

    pub fn delete_file(self, path: impl AsRef<Path>) -> Result<Self> {
        let path = normalize_path(&*self.root, path)?;
        let operation = Arc::new(DeleteFileOperation::new(path)?);
        
        match self.state {
            State::InTransaction(_) => {
                self.apply_transition(Transition::AddOperation(operation))
            },
            State::Idle => {
                self.begin_transaction()?
                    .apply_transition(Transition::AddOperation(operation))?
                    .commit()
            }
        }
    }

    pub fn create_dir(self, path: impl AsRef<Path>) -> Result<Self> {
        let path = normalize_path(&*self.root, path)?;
        match self.state {
            State::InTransaction(_) => {
                let operation = Arc::new(CreateFileOperation::new(path, String::new()));
                self.apply_transition(Transition::AddOperation(operation))
            },
            State::Idle => {
                std::fs::create_dir_all(&path)
                    .map_err(|e| fs_err!("ディレクトリの作成に失敗: {}: {}", path.display(), e))?;
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