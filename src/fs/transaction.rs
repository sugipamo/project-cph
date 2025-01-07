use std::path::{Path, PathBuf};
use std::sync::Arc;
use anyhow::Error;
use crate::error::fs::io_error as create_io_error;

pub trait FileOperation: Send + Sync + std::fmt::Debug {
    fn execute(&self) -> Result<(), Error>;
    fn rollback(&self) -> Result<(), Error>;
    fn description(&self) -> String;
    fn validate(&self) -> Result<(), Error>;
}

#[derive(Debug, Clone)]
pub enum TransactionState {
    Pending,
    Executed,
    RolledBack,
    Failed(Arc<Error>),
}

#[derive(Debug, Clone)]
pub enum TransactionTransition {
    AddOperation(Arc<dyn FileOperation>),
    Execute,
    Rollback,
}

#[derive(Debug, Clone)]
pub struct FileTransaction {
    operations: Arc<Vec<Arc<dyn FileOperation>>>,
    state: TransactionState,
}

impl FileTransaction {
    pub fn new() -> Self {
        Self {
            operations: Arc::new(Vec::new()),
            state: TransactionState::Pending,
        }
    }

    fn with_operations(&self, operations: Vec<Arc<dyn FileOperation>>) -> Self {
        Self {
            operations: Arc::new(operations),
            state: self.state.clone(),
        }
    }

    fn with_state(&self, state: TransactionState) -> Self {
        Self {
            operations: self.operations.clone(),
            state,
        }
    }

    pub fn apply_transition(self, transition: TransactionTransition) -> Result<Self, Error> {
        match (self.state.clone(), transition.clone()) {
            (TransactionState::Pending, TransactionTransition::AddOperation(op)) => {
                if let Err(e) = op.validate() {
                    return Err(create_io_error(
                        std::io::Error::new(
                            std::io::ErrorKind::InvalidInput,
                            format!("操作の検証に失敗: {}", e)
                        ),
                        "操作の検証に失敗"
                    ));
                }

                let operations = Arc::new(
                    self.operations.iter()
                        .cloned()
                        .chain(std::iter::once(op))
                        .collect::<Vec<_>>()
                );
                Ok(Self { operations, state: self.state })
            },
            (TransactionState::Pending, TransactionTransition::Execute) => {
                for operation in self.operations.iter() {
                    if let Err(e) = operation.execute() {
                        let failed_state = Self {
                            operations: self.operations.clone(),
                            state: TransactionState::Failed(Arc::new(e))
                        };
                        return Ok(failed_state.apply_transition(TransactionTransition::Rollback)?);
                    }
                }
                Ok(Self {
                    operations: self.operations,
                    state: TransactionState::Executed
                })
            },
            (TransactionState::Executed | TransactionState::Pending, TransactionTransition::Rollback) => {
                for operation in self.operations.iter().rev() {
                    if let Err(e) = operation.rollback() {
                        return Ok(Self {
                            operations: self.operations.clone(),
                            state: TransactionState::Failed(Arc::new(e))
                        });
                    }
                }
                Ok(Self {
                    operations: self.operations,
                    state: TransactionState::RolledBack
                })
            },
            (state, transition) => {
                let error = create_io_error(
                    std::io::Error::new(
                        std::io::ErrorKind::InvalidInput,
                        format!("無効な状態遷移: {:?} -> {:?}", state, transition)
                    ),
                    "トランザクション状態遷移エラー"
                );
                Ok(Self {
                    operations: self.operations,
                    state: TransactionState::Failed(Arc::new(error))
                })
            }
        }
    }

    // 公開APIメソッド
    pub fn with_operation(self, operation: Arc<dyn FileOperation>) -> Result<Self, Error> {
        self.apply_transition(TransactionTransition::AddOperation(operation))
    }

    pub fn execute(self) -> Result<Self, Error> {
        self.apply_transition(TransactionTransition::Execute)
    }

    pub fn rollback(self) -> Result<Self, Error> {
        self.apply_transition(TransactionTransition::Rollback)
    }

    pub fn state(&self) -> &TransactionState {
        &self.state
    }

    pub fn operations(&self) -> &[Arc<dyn FileOperation>] {
        &self.operations
    }

    // トランザクションの合成メソッド
    pub fn combine(self, other: Self) -> Result<Self, Error> {
        match (self.state.clone(), other.state) {
            (TransactionState::Pending, TransactionState::Pending) => {
                let operations = Arc::new(
                    self.operations.iter()
                        .chain(other.operations.iter())
                        .cloned()
                        .collect::<Vec<_>>()
                );
                Ok(Self {
                    operations,
                    state: TransactionState::Pending,
                })
            },
            _ => {
                let error = create_io_error(
                    std::io::Error::new(
                        std::io::ErrorKind::InvalidInput,
                        "トランザクションの合成は保留状態でのみ可能です"
                    ),
                    "トランザクション合成エラー"
                );
                Ok(Self {
                    operations: self.operations,
                    state: TransactionState::Failed(Arc::new(error))
                })
            }
        }
    }
}

// イミュータブルな操作を実装するための具体的な型
#[derive(Debug)]
pub struct CreateFileOperation {
    path: Arc<PathBuf>,
    content: Arc<String>,
}

impl CreateFileOperation {
    pub fn new(path: PathBuf, content: String) -> Self {
        Self {
            path: Arc::new(path),
            content: Arc::new(content),
        }
    }
}

impl FileOperation for CreateFileOperation {
    fn execute(&self) -> Result<(), Error> {
        if let Some(parent) = self.path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| create_io_error(e, format!("ディレクトリの作成に失敗: {}", parent.display())))?;
        }
        std::fs::write(&*self.path, &*self.content)
            .map_err(|e| create_io_error(e, format!("ファイルの書き込みに失敗: {}", self.path.display())))
    }

    fn rollback(&self) -> Result<(), Error> {
        if self.path.exists() {
            std::fs::remove_file(&*self.path)
                .map_err(|e| create_io_error(e, format!("ファイルの削除に失敗: {}", self.path.display())))?;
        }
        Ok(())
    }

    fn description(&self) -> String {
        format!("ファイル作成: {}", self.path.display())
    }

    fn validate(&self) -> Result<(), Error> {
        if self.path.exists() {
            return Err(create_io_error(
                std::io::Error::new(
                    std::io::ErrorKind::AlreadyExists,
                    format!("ファイルが既に存在します: {}", self.path.display())
                ),
                "ファイル作成の検証に失敗"
            ));
        }
        Ok(())
    }
}

#[derive(Debug)]
pub struct DeleteFileOperation {
    path: Arc<PathBuf>,
    original_content: Option<Arc<String>>,
}

impl DeleteFileOperation {
    pub fn new(path: PathBuf) -> Result<Self, Error> {
        let original_content = if path.exists() {
            Some(Arc::new(std::fs::read_to_string(&path)
                .map_err(|e| create_io_error(e, format!("ファイルの読み込みに失敗: {}", path.display())))?))
        } else {
            None
        };

        Ok(Self {
            path: Arc::new(path),
            original_content,
        })
    }
}

impl FileOperation for DeleteFileOperation {
    fn execute(&self) -> Result<(), Error> {
        if self.path.exists() {
            std::fs::remove_file(&*self.path)
                .map_err(|e| create_io_error(e, format!("ファイルの削除に失敗: {}", self.path.display())))?;
        }
        Ok(())
    }

    fn rollback(&self) -> Result<(), Error> {
        if let Some(content) = &self.original_content {
            if let Some(parent) = self.path.parent() {
                std::fs::create_dir_all(parent)
                    .map_err(|e| create_io_error(e, format!("ディレクトリの作成に失敗: {}", parent.display())))?;
            }
            std::fs::write(&*self.path, &**content)
                .map_err(|e| create_io_error(e, format!("ファイルの復元に失敗: {}", self.path.display())))?;
        }
        Ok(())
    }

    fn description(&self) -> String {
        format!("ファイル削除: {}", self.path.display())
    }

    fn validate(&self) -> Result<(), Error> {
        if !self.path.exists() {
            return Err(create_io_error(
                std::io::Error::new(
                    std::io::ErrorKind::NotFound,
                    format!("ファイルが存在しません: {}", self.path.display())
                ),
                "ファイル削除の検証に失敗"
            ));
        }
        Ok(())
    }
} 
