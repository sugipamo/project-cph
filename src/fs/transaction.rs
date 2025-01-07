use std::path::PathBuf;
use std::sync::Arc;
use crate::error::Error;
use crate::fs::error::io_err;

pub trait FileOperation: Send + Sync + std::fmt::Debug {
    fn execute(&self) -> Result<(), Error>;
    fn rollback(&self) -> Result<(), Error>;
    fn description(&self) -> String;
}

// 状態遷移を表現する型
#[derive(Debug, Clone)]
pub enum TransactionTransition {
    AddOperation(Arc<dyn FileOperation>),
    Execute,
    Rollback,
}

#[derive(Debug, Clone)]
pub enum TransactionState {
    Pending,
    Executed,
    RolledBack,
    Failed(Arc<Error>),
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

    // 状態遷移を適用するメソッド
    pub fn apply_transition(self, transition: TransactionTransition) -> Result<Self, Error> {
        match (self.state, transition) {
            (TransactionState::Pending, TransactionTransition::AddOperation(op)) => {
                let mut operations = (*self.operations).clone();
                operations.push(op);
                Ok(Self {
                    operations: Arc::new(operations),
                    state: TransactionState::Pending,
                })
            },
            (TransactionState::Pending, TransactionTransition::Execute) => {
                let operations = self.operations.clone();
                for operation in operations.iter() {
                    if let Err(e) = operation.execute() {
                        let failed_state = Self {
                            operations: operations.clone(),
                            state: TransactionState::Failed(Arc::new(e)),
                        };
                        return Ok(failed_state.apply_transition(TransactionTransition::Rollback)?);
                    }
                }
                Ok(Self {
                    operations,
                    state: TransactionState::Executed,
                })
            },
            (TransactionState::Executed | TransactionState::Pending, TransactionTransition::Rollback) => {
                let operations = self.operations.clone();
                for operation in operations.iter().rev() {
                    if let Err(e) = operation.rollback() {
                        return Ok(Self {
                            operations,
                            state: TransactionState::Failed(Arc::new(e)),
                        });
                    }
                }
                Ok(Self {
                    operations,
                    state: TransactionState::RolledBack,
                })
            },
            (state, transition) => {
                Ok(Self {
                    operations: self.operations,
                    state: TransactionState::Failed(Arc::new(io_err(
                        std::io::Error::new(
                            std::io::ErrorKind::InvalidInput,
                            format!("無効な状態遷移: {:?} -> {:?}", state, transition)
                        ),
                        "トランザクション状態遷移エラー".to_string(),
                    ))),
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
        match (self.state, other.state) {
            (TransactionState::Pending, TransactionState::Pending) => {
                let mut operations = (*self.operations).clone();
                operations.extend((*other.operations).clone());
                Ok(Self {
                    operations: Arc::new(operations),
                    state: TransactionState::Pending,
                })
            },
            _ => Err(io_err(
                std::io::Error::new(
                    std::io::ErrorKind::InvalidInput,
                    "トランザクションの合成は保留状態でのみ可能です"
                ),
                "トランザクション合成エラー".to_string(),
            )),
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
                .map_err(|e| io_err(e, format!("ディレクトリの作成に失敗: {}", parent.display())))?;
        }
        std::fs::write(&*self.path, &*self.content)
            .map_err(|e| io_err(e, format!("ファイルの書き込みに失敗: {}", self.path.display())))
    }

    fn rollback(&self) -> Result<(), Error> {
        if self.path.exists() {
            std::fs::remove_file(&*self.path)
                .map_err(|e| io_err(e, format!("ファイルの削除に失敗: {}", self.path.display())))?;
        }
        Ok(())
    }

    fn description(&self) -> String {
        format!("ファイル作成: {}", self.path.display())
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
                .map_err(|e| io_err(e, format!("ファイルの読み込みに失敗: {}", path.display())))?))
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
                .map_err(|e| io_err(e, format!("ファイルの削除に失敗: {}", self.path.display())))?;
        }
        Ok(())
    }

    fn rollback(&self) -> Result<(), Error> {
        if let Some(content) = &self.original_content {
            if let Some(parent) = self.path.parent() {
                std::fs::create_dir_all(parent)
                    .map_err(|e| io_err(e, format!("ディレクトリの作成に失敗: {}", parent.display())))?;
            }
            std::fs::write(&*self.path, &**content)
                .map_err(|e| io_err(e, format!("ファイルの復元に失敗: {}", self.path.display())))?;
        }
        Ok(())
    }

    fn description(&self) -> String {
        format!("ファイル削除: {}", self.path.display())
    }
} 
