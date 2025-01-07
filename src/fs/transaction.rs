use std::path::{Path, PathBuf};
use std::sync::Arc;
use anyhow::{Error, Result};
use crate::fs::error::{io_error, transaction_error, validation_error, ErrorExt};
use crate::fs::path::ensure_path_exists;

pub trait FileOperation: Send + Sync + std::fmt::Debug {
    fn execute(&self) -> Result<()>;
    fn rollback(&self) -> Result<()>;
    fn description(&self) -> String;
    fn validate(&self) -> Result<()>;
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

    pub fn apply_transition(self, transition: TransactionTransition) -> Result<Self> {
        match (self.state.clone(), transition.clone()) {
            (TransactionState::Pending, TransactionTransition::AddOperation(op)) => {
                if let Err(e) = op.validate() {
                    return Err(validation_error(format!("操作の検証に失敗: {}", e)));
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
                Err(transaction_error(format!("無効な状態遷移: {:?} -> {:?}", state, transition)))
            }
        }
    }

    // 公開APIメソッド
    pub fn with_operation(self, operation: Arc<dyn FileOperation>) -> Result<Self> {
        self.apply_transition(TransactionTransition::AddOperation(operation))
    }

    pub fn execute(self) -> Result<Self> {
        self.apply_transition(TransactionTransition::Execute)
    }

    pub fn rollback(self) -> Result<Self> {
        self.apply_transition(TransactionTransition::Rollback)
    }

    pub fn state(&self) -> &TransactionState {
        &self.state
    }

    pub fn operations(&self) -> &[Arc<dyn FileOperation>] {
        &self.operations
    }

    // トランザクションの合成メソッド
    pub fn combine(self, other: Self) -> Result<Self> {
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
                Err(transaction_error("トランザクションの合成は保留状態でのみ可能です"))
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
    fn execute(&self) -> Result<()> {
        if let Some(parent) = self.path.parent() {
            ensure_path_exists(parent)?;
        }
        std::fs::write(&*self.path, &*self.content)
            .with_context_io(format!("ファイルの書き込みに失敗: {}", self.path.display()))
    }

    fn rollback(&self) -> Result<()> {
        if self.path.exists() {
            std::fs::remove_file(&*self.path)
                .with_context_io(format!("ファイルの削除に失敗: {}", self.path.display()))?;
        }
        Ok(())
    }

    fn description(&self) -> String {
        format!("ファイル作成: {}", self.path.display())
    }

    fn validate(&self) -> Result<()> {
        if self.path.exists() {
            return Err(validation_error(format!("ファイルが既に存在します: {}", self.path.display())));
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
    pub fn new(path: PathBuf) -> Result<Self> {
        let original_content = if path.exists() {
            Some(Arc::new(std::fs::read_to_string(&path)
                .with_context_io(format!("ファイルの読み込みに失敗: {}", path.display()))?))
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
    fn execute(&self) -> Result<()> {
        if self.path.exists() {
            std::fs::remove_file(&*self.path)
                .with_context_io(format!("ファイルの削除に失敗: {}", self.path.display()))?;
        }
        Ok(())
    }

    fn rollback(&self) -> Result<()> {
        if let Some(content) = &self.original_content {
            if let Some(parent) = self.path.parent() {
                ensure_path_exists(parent)?;
            }
            std::fs::write(&*self.path, &**content)
                .with_context_io(format!("ファイルの復元に失敗: {}", self.path.display()))?;
        }
        Ok(())
    }

    fn description(&self) -> String {
        format!("ファイル削除: {}", self.path.display())
    }

    fn validate(&self) -> Result<()> {
        if !self.path.exists() {
            return Err(validation_error(format!("ファイルが存在しません: {}", self.path.display())));
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::fs::tests::TestDirectory;

    #[test]
    fn test_file_operations() -> Result<()> {
        let test_dir = TestDirectory::new()?;
        
        // CreateFileOperationのテスト
        let file_path = test_dir.path().join("test.txt");
        let create_op = CreateFileOperation::new(file_path.clone(), "Hello, World!".to_string());
        
        create_op.execute()?;
        assert!(file_path.exists());
        assert_eq!(std::fs::read_to_string(&file_path)?, "Hello, World!");
        
        create_op.rollback()?;
        assert!(!file_path.exists());
        
        // DeleteFileOperationのテスト
        std::fs::write(&file_path, "Test content")?;
        let delete_op = DeleteFileOperation::new(file_path.clone())?;
        
        delete_op.execute()?;
        assert!(!file_path.exists());
        
        delete_op.rollback()?;
        assert!(file_path.exists());
        assert_eq!(std::fs::read_to_string(&file_path)?, "Test content");
        
        Ok(())
    }

    #[test]
    fn test_transaction() -> Result<()> {
        let test_dir = TestDirectory::new()?;
        let file1_path = test_dir.path().join("file1.txt");
        let file2_path = test_dir.path().join("file2.txt");
        
        let mut transaction = FileTransaction::new();
        
        // 操作の追加
        transaction = transaction.with_operation(Arc::new(
            CreateFileOperation::new(file1_path.clone(), "File 1".to_string())
        ))?;
        
        transaction = transaction.with_operation(Arc::new(
            CreateFileOperation::new(file2_path.clone(), "File 2".to_string())
        ))?;
        
        // トランザクションの実行
        transaction = transaction.execute()?;
        assert!(file1_path.exists());
        assert!(file2_path.exists());
        
        // ロールバック
        transaction = transaction.rollback()?;
        assert!(!file1_path.exists());
        assert!(!file2_path.exists());
        
        Ok(())
    }
} 
