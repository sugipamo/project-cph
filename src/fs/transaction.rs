use std::path::{Path, PathBuf};
use std::sync::Arc;
use crate::error::Error;
use crate::fs::error::{io_err, not_found_err};

pub trait FileOperation: Send + Sync + std::fmt::Debug {
    fn execute(&self) -> Result<(), Error>;
    fn rollback(&self) -> Result<(), Error>;
    fn description(&self) -> String;
}

#[derive(Debug, Clone)]
pub struct FileTransaction {
    operations: Arc<Vec<Arc<dyn FileOperation>>>,
    executed: bool,
}

impl FileTransaction {
    pub fn new() -> Self {
        Self {
            operations: Arc::new(Vec::new()),
            executed: false,
        }
    }

    pub fn with_operation(mut self, operation: Arc<dyn FileOperation>) -> Self {
        let mut operations = Arc::get_mut(&mut self.operations)
            .expect("FileTransactionのoperationsが他で参照されています")
            .clone();
        operations.push(operation);
        self.operations = Arc::new(operations);
        self
    }

    pub fn execute(&mut self) -> Result<(), Error> {
        if self.executed {
            return Ok(());
        }

        for operation in self.operations.iter() {
            if let Err(e) = operation.execute() {
                self.rollback()?;
                return Err(e);
            }
        }

        self.executed = true;
        Ok(())
    }

    pub fn rollback(&self) -> Result<(), Error> {
        for operation in self.operations.iter().rev() {
            if let Err(e) = operation.rollback() {
                return Err(e);
            }
        }
        Ok(())
    }

    pub fn is_executed(&self) -> bool {
        self.executed
    }

    pub fn operations(&self) -> &[Arc<dyn FileOperation>] {
        &self.operations
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
