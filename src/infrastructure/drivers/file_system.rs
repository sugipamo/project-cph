use crate::interfaces::file_system::FileSystem;
use anyhow::Result;
use std::path::Path;
use tokio::fs;

pub struct LocalFileSystem;

impl LocalFileSystem {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait::async_trait]
impl FileSystem for LocalFileSystem {
    async fn read(&self, path: &Path) -> Result<String> {
        Ok(fs::read_to_string(path).await?)
    }

    async fn write(&self, path: &Path, content: &str) -> Result<()> {
        Ok(fs::write(path, content).await?)
    }

    async fn exists(&self, path: &Path) -> Result<bool> {
        Ok(path.exists())
    }

    async fn create_dir(&self, path: &Path) -> Result<()> {
        Ok(fs::create_dir_all(path).await?)
    }

    async fn remove(&self, path: &Path) -> Result<()> {
        if path.is_dir() {
            Ok(fs::remove_dir_all(path).await?)
        } else {
            Ok(fs::remove_file(path).await?)
        }
    }

    async fn copy(&self, from: &Path, to: &Path) -> Result<()> {
        Ok(fs::copy(from, to).await.map(|_| ())?)
    }

    async fn list_dir(&self, path: &Path) -> Result<Vec<std::path::PathBuf>> {
        let mut entries = fs::read_dir(path).await?;
        let mut paths = Vec::new();
        
        while let Some(entry) = entries.next_entry().await? {
            paths.push(entry.path());
        }
        
        Ok(paths)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[tokio::test]
    async fn test_local_file_system_write_and_read() {
        let temp_dir = TempDir::new().unwrap();
        let fs = LocalFileSystem::new();
        let file_path = temp_dir.path().join("test.txt");
        let content = "Hello, World!";

        // Write file
        fs.write(&file_path, content).await.unwrap();

        // Read file
        let read_content = fs.read(&file_path).await.unwrap();
        assert_eq!(read_content, content);
    }

    #[tokio::test]
    async fn test_local_file_system_exists() {
        let temp_dir = TempDir::new().unwrap();
        let fs = LocalFileSystem::new();
        let file_path = temp_dir.path().join("test.txt");

        // File doesn't exist yet
        assert!(!fs.exists(&file_path).await.unwrap());

        // Create file
        fs.write(&file_path, "test").await.unwrap();

        // File should exist now
        assert!(fs.exists(&file_path).await.unwrap());
    }

    #[tokio::test]
    async fn test_local_file_system_create_dir() {
        let temp_dir = TempDir::new().unwrap();
        let fs = LocalFileSystem::new();
        let dir_path = temp_dir.path().join("nested/directory");

        // Create nested directory
        fs.create_dir(&dir_path).await.unwrap();

        // Directory should exist
        assert!(fs.exists(&dir_path).await.unwrap());
    }

    #[tokio::test]
    async fn test_local_file_system_remove() {
        let temp_dir = TempDir::new().unwrap();
        let fs = LocalFileSystem::new();
        let file_path = temp_dir.path().join("test.txt");

        // Create and remove file
        fs.write(&file_path, "test").await.unwrap();
        assert!(fs.exists(&file_path).await.unwrap());
        
        fs.remove(&file_path).await.unwrap();
        assert!(!fs.exists(&file_path).await.unwrap());
    }

    #[tokio::test]
    async fn test_local_file_system_copy() {
        let temp_dir = TempDir::new().unwrap();
        let fs = LocalFileSystem::new();
        let source = temp_dir.path().join("source.txt");
        let dest = temp_dir.path().join("dest.txt");
        let content = "Copy me!";

        // Create source file
        fs.write(&source, content).await.unwrap();

        // Copy file
        fs.copy(&source, &dest).await.unwrap();

        // Both files should exist with same content
        assert!(fs.exists(&source).await.unwrap());
        assert!(fs.exists(&dest).await.unwrap());
        assert_eq!(fs.read(&dest).await.unwrap(), content);
    }

    #[tokio::test]
    async fn test_local_file_system_list_dir() {
        let temp_dir = TempDir::new().unwrap();
        let fs = LocalFileSystem::new();

        // Create some files
        fs.write(&temp_dir.path().join("file1.txt"), "1").await.unwrap();
        fs.write(&temp_dir.path().join("file2.txt"), "2").await.unwrap();
        fs.create_dir(&temp_dir.path().join("subdir")).await.unwrap();

        // List directory
        let entries = fs.list_dir(temp_dir.path()).await.unwrap();
        assert_eq!(entries.len(), 3);
    }
}