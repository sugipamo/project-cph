use crate::error::{CphError, FileSystemError, Result};

pub trait FileOperation {
    fn execute(&self) -> Result<()>;
    fn rollback(&self) -> Result<()>;
}

pub struct Transaction {
    operations: Vec<Box<dyn FileOperation>>,
    executed: bool,
}

impl Transaction {
    pub fn new() -> Self {
        Self {
            operations: Vec::new(),
            executed: false,
        }
    }

    pub fn add_operation(&mut self, operation: Box<dyn FileOperation>) {
        self.operations.push(operation);
    }

    pub fn execute(&mut self) -> Result<()> {
        if self.executed {
            return Err(CphError::Fs(FileSystemError::NotFound {
                path: "トランザクションは既に実行されています".to_string()
            }));
        }

        let mut executed_operations = Vec::new();
        for operation in &self.operations {
            match operation.execute() {
                Ok(()) => executed_operations.push(operation),
                Err(e) => {
                    // ロールバック
                    for executed_operation in executed_operations.iter().rev() {
                        if let Err(rollback_err) = executed_operation.rollback() {
                            return Err(CphError::Fs(FileSystemError::Io(std::io::Error::new(
                                std::io::ErrorKind::Other,
                                format!("ロールバック中にエラーが発生しました: {}", rollback_err),
                            ))));
                        }
                    }
                    return Err(CphError::Fs(FileSystemError::Io(std::io::Error::new(
                        std::io::ErrorKind::Other,
                        format!("操作の実行中にエラーが発生しました: {}", e),
                    ))));
                }
            }
        }

        self.executed = true;
        Ok(())
    }
} 
