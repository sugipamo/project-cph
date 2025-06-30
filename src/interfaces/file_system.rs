use anyhow::Result;
use std::path::Path;

#[async_trait::async_trait]
pub trait FileSystem: Send + Sync {
    async fn read(&self, path: &Path) -> Result<String>;
    async fn write(&self, path: &Path, content: &str) -> Result<()>;
    async fn exists(&self, path: &Path) -> Result<bool>;
    async fn create_dir(&self, path: &Path) -> Result<()>;
    async fn remove(&self, path: &Path) -> Result<()>;
    async fn copy(&self, from: &Path, to: &Path) -> Result<()>;
    async fn list_dir(&self, path: &Path) -> Result<Vec<std::path::PathBuf>>;
}