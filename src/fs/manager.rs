use std::path::{Path, PathBuf};
use crate::error::CphError;
use crate::fs::error::{io_err, not_found_err};

pub struct FileManager {
    root_dir: PathBuf,
}

impl FileManager {
    pub fn new<P: AsRef<Path>>(root_dir: P) -> Result<Self, CphError> {
        let root_dir = root_dir.as_ref().to_path_buf();
        if !root_dir.exists() {
            std::fs::create_dir_all(&root_dir)
                .map_err(|e| io_err(e, "ルートディレクトリの作成に失敗".to_string()))?;
        }
        Ok(Self { root_dir })
    }

    pub fn get_root_dir(&self) -> &Path {
        &self.root_dir
    }

    pub fn create_directory<P: AsRef<Path>>(&self, path: P) -> Result<PathBuf, CphError> {
        let full_path = self.root_dir.join(path);
        std::fs::create_dir_all(&full_path)
            .map_err(|e| io_err(e, format!("ディレクトリの作成に失敗: {}", full_path.display())))?;
        Ok(full_path)
    }

    pub fn write_file<P: AsRef<Path>>(&self, path: P, content: &str) -> Result<PathBuf, CphError> {
        let full_path = self.root_dir.join(path);
        if let Some(parent) = full_path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| io_err(e, format!("親ディレクトリの作成に失敗: {}", parent.display())))?;
        }
        std::fs::write(&full_path, content)
            .map_err(|e| io_err(e, format!("ファイルの書き込みに失敗: {}", full_path.display())))?;
        Ok(full_path)
    }

    pub fn read_file<P: AsRef<Path>>(&self, path: P) -> Result<String, CphError> {
        let full_path = self.root_dir.join(path);
        if !full_path.exists() {
            return Err(not_found_err(full_path.to_string_lossy().to_string()));
        }
        std::fs::read_to_string(&full_path)
            .map_err(|e| io_err(e, format!("ファイルの読み込みに失敗: {}", full_path.display())))
    }

    pub fn remove_file<P: AsRef<Path>>(&self, path: P) -> Result<(), CphError> {
        let full_path = self.root_dir.join(path);
        if !full_path.exists() {
            return Ok(());
        }
        std::fs::remove_file(&full_path)
            .map_err(|e| io_err(e, format!("ファイルの削除に失敗: {}", full_path.display())))
    }

    pub fn remove_directory<P: AsRef<Path>>(&self, path: P) -> Result<(), CphError> {
        let full_path = self.root_dir.join(path);
        if !full_path.exists() {
            return Ok(());
        }
        std::fs::remove_dir_all(&full_path)
            .map_err(|e| io_err(e, format!("ディレクトリの削除に失敗: {}", full_path.display())))
    }
} 