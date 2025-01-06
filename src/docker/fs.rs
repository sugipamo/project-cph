use std::path::{Path, PathBuf};
use crate::docker::error::{DockerError, DockerResult};
use crate::fs::{FileManager, DockerFileOperations};

pub struct DefaultDockerFileManager {
    file_manager: FileManager,
}

impl DefaultDockerFileManager {
    pub fn new() -> DockerResult<Self> {
        Ok(Self {
            file_manager: FileManager::new().map_err(|e| DockerError::Filesystem(e.to_string()))?,
        })
    }
}

impl DockerFileManager for DefaultDockerFileManager {
    fn create_temp_directory(&self) -> DockerResult<PathBuf> {
        self.file_manager
            .create_temp_directory()
            .map_err(|e| DockerError::Filesystem(e.to_string()))
    }

    fn write_source_file(&self, dir: &Path, filename: &str, content: &str) -> DockerResult<PathBuf> {
        self.file_manager
            .write_source_file(dir, filename, content)
            .map_err(|e| DockerError::Filesystem(e.to_string()))
    }

    fn set_permissions(&self, path: &Path, mode: u32) -> DockerResult<()> {
        self.file_manager
            .set_permissions(path, mode)
            .map_err(|e| DockerError::Filesystem(e.to_string()))
    }

    fn cleanup(&self, dir: &Path) -> DockerResult<()> {
        if dir.exists() {
            std::fs::remove_dir_all(dir)
                .map_err(|e| DockerError::Filesystem(e.to_string()))?;
        }
        Ok(())
    }
}

pub trait DockerFileManager {
    fn create_temp_directory(&self) -> DockerResult<PathBuf>;
    fn write_source_file(&self, dir: &Path, filename: &str, content: &str) -> DockerResult<PathBuf>;
    fn set_permissions(&self, path: &Path, mode: u32) -> DockerResult<()>;
    fn cleanup(&self, dir: &Path) -> DockerResult<()>;
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn test_docker_file_manager() -> DockerResult<()> {
        let manager = DefaultDockerFileManager::new()?;
        
        // 一時ディレクトリの作成
        let temp_dir = manager.create_temp_directory()?;
        assert!(temp_dir.exists());

        // ソースファイルの書き込み
        let file_path = manager.write_source_file(&temp_dir, "test.txt", "test content")?;
        assert!(file_path.exists());
        let content = fs::read_to_string(&file_path)
            .map_err(|e| DockerError::Filesystem(e.to_string()))?;
        assert_eq!(content, "test content");

        // 権限設定
        manager.set_permissions(&temp_dir, 0o777)?;
        let metadata = fs::metadata(&temp_dir)
            .map_err(|e| DockerError::Filesystem(e.to_string()))?;
        assert_eq!(metadata.permissions().mode() & 0o777, 0o777);

        // クリーンアップ
        manager.cleanup(&temp_dir)?;
        assert!(!temp_dir.exists());

        Ok(())
    }
} 