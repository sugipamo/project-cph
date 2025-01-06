use std::path::{Path, PathBuf};
use crate::error::CphError;
use crate::fs::error::{io_err, not_found_err};

pub struct FileTransaction {
    operations: Vec<Box<dyn FileOperation>>,
    executed: bool,
}

impl FileTransaction {
    pub fn new() -> Self {
        Self {
            operations: Vec::new(),
            executed: false,
        }
    }

    pub fn add_operation(&mut self, operation: Box<dyn FileOperation>) {
        self.operations.push(operation);
    }

    pub fn execute(&mut self) -> Result<(), CphError> {
        if self.executed {
            return Ok(());
        }

        for operation in &self.operations {
            if let Err(e) = operation.execute() {
                self.rollback()?;
                return Err(e);
            }
        }

        self.executed = true;
        Ok(())
    }

    pub fn rollback(&mut self) -> Result<(), CphError> {
        for operation in self.operations.iter().rev() {
            if let Err(e) = operation.rollback() {
                return Err(io_err(
                    std::io::Error::new(std::io::ErrorKind::Other, e.to_string()),
                    "トランザクションのロールバック中にエラーが発生".to_string(),
                ));
            }
        }
        self.executed = false;
        Ok(())
    }
}

pub trait FileOperation: Send + Sync {
    fn execute(&self) -> Result<(), CphError>;
    fn rollback(&self) -> Result<(), CphError>;
}

pub struct CopyOperation {
    source: PathBuf,
    destination: PathBuf,
}

impl CopyOperation {
    pub fn new<P: AsRef<Path>>(source: P, destination: P) -> Self {
        Self {
            source: source.as_ref().to_path_buf(),
            destination: destination.as_ref().to_path_buf(),
        }
    }
}

impl FileOperation for CopyOperation {
    fn execute(&self) -> Result<(), CphError> {
        if !self.source.exists() {
            return Err(not_found_err(self.source.to_string_lossy().to_string()));
        }

        if let Some(parent) = self.destination.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| io_err(e, format!("親ディレクトリの作成に失敗: {}", parent.display())))?;
        }

        std::fs::copy(&self.source, &self.destination)
            .map_err(|e| io_err(e, format!("ファイルのコピーに失敗: {} -> {}", 
                self.source.display(), self.destination.display())))?;
        Ok(())
    }

    fn rollback(&self) -> Result<(), CphError> {
        if self.destination.exists() {
            std::fs::remove_file(&self.destination)
                .map_err(|e| io_err(e, format!("ファイルの削除に失敗: {}", self.destination.display())))?;
        }
        Ok(())
    }
}

pub struct CreateDirectoryOperation {
    path: PathBuf,
}

impl CreateDirectoryOperation {
    pub fn new<P: AsRef<Path>>(path: P) -> Self {
        Self {
            path: path.as_ref().to_path_buf(),
        }
    }
}

impl FileOperation for CreateDirectoryOperation {
    fn execute(&self) -> Result<(), CphError> {
        std::fs::create_dir_all(&self.path)
            .map_err(|e| io_err(e, format!("ディレクトリの作成に失敗: {}", self.path.display())))?;
        Ok(())
    }

    fn rollback(&self) -> Result<(), CphError> {
        if self.path.exists() {
            std::fs::remove_dir_all(&self.path)
                .map_err(|e| io_err(e, format!("ディレクトリの削除に失敗: {}", self.path.display())))?;
        }
        Ok(())
    }
} 
