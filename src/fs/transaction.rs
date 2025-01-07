use std::path::PathBuf;
use std::sync::Arc;
use std::time::SystemTime;
use crate::error::Error;
use crate::fs::error::helpers::create_io_error;

pub trait FileOperation: Send + Sync + std::fmt::Debug {
    fn execute(&self) -> Result<(), Error>;
    fn rollback(&self) -> Result<(), Error>;
    fn description(&self) -> String;
    fn validate(&self) -> Result<(), Error>;
}

#[derive(Debug, Clone)]
pub struct TransactionHistory {
    timestamp: SystemTime,
    transition: TransactionTransition,
    result: TransactionResult,
}

#[derive(Debug, Clone)]
pub enum TransactionResult {
    Success,
    Failure(String),
}

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
    history: Arc<Vec<TransactionHistory>>,
}

impl FileTransaction {
    pub fn new() -> Self {
        Self {
            operations: Arc::new(Vec::new()),
            state: TransactionState::Pending,
            history: Arc::new(Vec::new()),
        }
    }

    fn with_transition_record(&self, transition: TransactionTransition, result: TransactionResult) -> Self {
        let mut history = (*self.history).clone();
        history.push(TransactionHistory {
            timestamp: SystemTime::now(),
            transition,
            result,
        });
        Self {
            operations: self.operations.clone(),
            state: self.state.clone(),
            history: Arc::new(history),
        }
    }

    fn with_operations(&self, operations: Vec<Arc<dyn FileOperation>>) -> Self {
        Self {
            operations: Arc::new(operations),
            state: self.state.clone(),
            history: self.history.clone(),
        }
    }

    fn with_state(&self, state: TransactionState) -> Self {
        Self {
            operations: self.operations.clone(),
            state,
            history: self.history.clone(),
        }
    }

    pub fn apply_transition(self, transition: TransactionTransition) -> Result<Self, Error> {
        match (self.state.clone(), transition.clone()) {
            (TransactionState::Pending, TransactionTransition::AddOperation(op)) => {
                if let Err(e) = op.validate() {
                    return Ok(self.with_transition_record(
                        transition,
                        TransactionResult::Failure(format!("操作の検証に失敗: {}", e))
                    ));
                }

                let mut operations = (*self.operations).clone();
                operations.push(op);
                Ok(self.with_transition_record(
                    transition,
                    TransactionResult::Success
                ).with_operations(operations))
            },
            (TransactionState::Pending, TransactionTransition::Execute) => {
                let operations = self.operations.clone();
                for operation in operations.iter() {
                    if let Err(e) = operation.execute() {
                        let failed_state = self.with_transition_record(
                            transition.clone(),
                            TransactionResult::Failure(format!("実行に失敗: {}", e))
                        ).with_state(TransactionState::Failed(Arc::new(e)));
                        return Ok(failed_state.apply_transition(TransactionTransition::Rollback)?);
                    }
                }
                Ok(self.with_transition_record(
                    transition,
                    TransactionResult::Success
                ).with_state(TransactionState::Executed))
            },
            (TransactionState::Executed | TransactionState::Pending, TransactionTransition::Rollback) => {
                let operations = self.operations.clone();
                for operation in operations.iter().rev() {
                    if let Err(e) = operation.rollback() {
                        return Ok(self.with_transition_record(
                            transition,
                            TransactionResult::Failure(format!("ロールバックに失敗: {}", e))
                        ).with_state(TransactionState::Failed(Arc::new(e))));
                    }
                }
                Ok(self.with_transition_record(
                    transition,
                    TransactionResult::Success
                ).with_state(TransactionState::RolledBack))
            },
            (state, transition) => {
                let error = create_io_error(
                    std::io::Error::new(
                        std::io::ErrorKind::InvalidInput,
                        format!("無効な状態遷移: {:?} -> {:?}", state, transition)
                    ),
                    "トランザクション状態遷移エラー"
                );
                Ok(self.with_transition_record(
                    transition,
                    TransactionResult::Failure(error.to_string())
                ).with_state(TransactionState::Failed(Arc::new(error))))
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

    pub fn history(&self) -> &[TransactionHistory] {
        &self.history
    }

    // トランザクションの合成メソッド
    pub fn combine(self, other: Self) -> Result<Self, Error> {
        match (self.state.clone(), other.state) {
            (TransactionState::Pending, TransactionState::Pending) => {
                let mut operations = (*self.operations).clone();
                operations.extend((*other.operations).clone());
                let mut history = (*self.history).clone();
                history.extend((*other.history).clone());
                Ok(Self {
                    operations: Arc::new(operations),
                    state: TransactionState::Pending,
                    history: Arc::new(history),
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
                Ok(self.with_transition_record(
                    TransactionTransition::Execute,
                    TransactionResult::Failure(error.to_string())
                ).with_state(TransactionState::Failed(Arc::new(error))))
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
