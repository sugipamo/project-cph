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