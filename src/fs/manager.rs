use std::path::PathBuf;
use crate::error::{CphError, FileSystemError, Result};

pub struct FileManager {
    root: PathBuf,
}

impl FileManager {
    pub fn new(root: PathBuf) -> Self {
        Self { root }
    }

    pub fn create_dir(&self, path: &str) -> Result<PathBuf> {
        let full_path = self.root.join(path);
        std::fs::create_dir_all(&full_path)
            .map_err(|e| CphError::Fs(FileSystemError::Io(std::io::Error::new(
                std::io::ErrorKind::Other,
                format!("ディレクトリの作成に失敗しました: {}", e),
            ))))?;
        Ok(full_path)
    }

    pub fn write_file(&self, path: &str, content: &str) -> Result<PathBuf> {
        let full_path = self.root.join(path);
        if let Some(parent) = full_path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| CphError::Fs(FileSystemError::Io(std::io::Error::new(
                    std::io::ErrorKind::Other,
                    format!("ディレクトリの作成に失敗しました: {}", e),
                ))))?;
        }
        std::fs::write(&full_path, content)
            .map_err(|e| CphError::Fs(FileSystemError::Io(std::io::Error::new(
                std::io::ErrorKind::Other,
                format!("ファイルの書き込みに失敗しました: {}", e),
            ))))?;
        Ok(full_path)
    }

    pub fn set_permissions(&self, path: &str, mode: u32) -> Result<()> {
        let full_path = self.root.join(path);
        let metadata = std::fs::metadata(&full_path)
            .map_err(|e| CphError::Fs(FileSystemError::Io(std::io::Error::new(
                std::io::ErrorKind::Other,
                format!("メタデータの取得に失敗しました: {}", e),
            ))))?;

        let mut perms = metadata.permissions();
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            perms.set_mode(mode);
        }
        std::fs::set_permissions(&full_path, perms)
            .map_err(|e| CphError::Fs(FileSystemError::Io(std::io::Error::new(
                std::io::ErrorKind::Other,
                format!("権限の設定に失敗しました: {}", e),
            ))))?;

        Ok(())
    }
} 