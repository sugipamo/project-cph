use std::path::{Path, PathBuf};
use super::error::{Result, FsError};
use super::FileOperation;

/// ディレクトリを作成する操作
#[derive(Debug)]
pub struct CreateDirOperation {
    path: PathBuf,
}

impl CreateDirOperation {
    /// 新しいディレクトリ作成操作を作成
    pub fn new<P: AsRef<Path>>(path: P) -> Self {
        Self {
            path: path.as_ref().to_path_buf(),
        }
    }
}

impl FileOperation for CreateDirOperation {
    fn execute(&self) -> Result<()> {
        std::fs::create_dir_all(&self.path)
            .map_err(|e| FsError::FileSystem {
                message: format!("ディレクトリの作成に失敗しました: {}", e),
                source: Some(e),
            })?;
        Ok(())
    }

    fn rollback(&self) -> Result<()> {
        if self.path.exists() {
            std::fs::remove_dir_all(&self.path)
                .map_err(|e| FsError::FileSystem {
                    message: format!("ディレクトリの削除に失敗しました: {}", e),
                    source: Some(e),
                })?;
        }
        Ok(())
    }
}

/// ファイルをコピーする操作
#[derive(Debug)]
pub struct CopyOperation {
    from: PathBuf,
    to: PathBuf,
}

impl CopyOperation {
    /// 新しいファイルコピー操作を作成
    pub fn new<P: AsRef<Path>>(from: P, to: P) -> Self {
        Self {
            from: from.as_ref().to_path_buf(),
            to: to.as_ref().to_path_buf(),
        }
    }
}

impl FileOperation for CopyOperation {
    fn execute(&self) -> Result<()> {
        std::fs::copy(&self.from, &self.to)
            .map_err(|e| FsError::FileSystem {
                message: format!("ファイルのコピーに失敗しました: {}", e),
                source: Some(e),
            })?;
        Ok(())
    }

    fn rollback(&self) -> Result<()> {
        if self.to.exists() {
            std::fs::remove_file(&self.to)
                .map_err(|e| FsError::FileSystem {
                    message: format!("ファイルの削除に失敗しました: {}", e),
                    source: Some(e),
                })?;
        }
        Ok(())
    }
}

/// ファイルを削除する操作
#[derive(Debug)]
pub struct RemoveOperation {
    path: PathBuf,
}

impl RemoveOperation {
    /// 新しいファイル削除操作を作成
    pub fn new<P: AsRef<Path>>(path: P) -> Self {
        Self {
            path: path.as_ref().to_path_buf(),
        }
    }
}

impl FileOperation for RemoveOperation {
    fn execute(&self) -> Result<()> {
        if self.path.exists() {
            std::fs::remove_file(&self.path)
                .map_err(|e| FsError::FileSystem {
                    message: format!("ファイルの削除に失敗しました: {}", e),
                    source: Some(e),
                })?;
        }
        Ok(())
    }

    fn rollback(&self) -> Result<()> {
        // 削除操作のロールバックは何もしない
        Ok(())
    }
}

/// ファイル操作のビルダー
#[derive(Debug, Default)]
pub struct FileOperationBuilder {
    operations: Vec<Box<dyn FileOperation>>,
}

impl FileOperationBuilder {
    /// 新しいビルダーを作成
    pub fn new() -> Self {
        Self {
            operations: Vec::new(),
        }
    }

    /// ディレクトリを作成する操作を追加
    pub fn create_dir<P: AsRef<Path>>(mut self, path: P) -> Self {
        self.operations.push(Box::new(CreateDirOperation::new(path)));
        self
    }

    /// ファイルをコピーする操作を追加
    pub fn copy_file<P: AsRef<Path>>(mut self, from: P, to: P) -> Self {
        self.operations.push(Box::new(CopyOperation::new(from, to)));
        self
    }

    /// ファイルを削除する操作を追加
    pub fn delete_file<P: AsRef<Path>>(mut self, path: P) -> Self {
        self.operations.push(Box::new(RemoveOperation::new(path)));
        self
    }

    /// 操作のリストを構築
    pub fn build(self) -> Vec<Box<dyn FileOperation>> {
        self.operations
    }
} 