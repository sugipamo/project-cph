use crate::infrastructure::test_support::{Expectation, Mock};
use anyhow::Result;
use std::collections::HashMap;
use std::path::{Path, PathBuf};

#[allow(clippy::unused_async)]

#[derive(Default)]
pub struct MockFileSystem {
    files: HashMap<PathBuf, String>,
    directories: Vec<PathBuf>,
    read_expectations: Vec<Expectation>,
    write_expectations: Vec<Expectation>,
}

impl MockFileSystem {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_file(mut self, path: impl Into<PathBuf>, content: impl Into<String>) -> Self {
        self.files.insert(path.into(), content.into());
        self
    }

    pub fn with_directory(mut self, path: impl Into<PathBuf>) -> Self {
        self.directories.push(path.into());
        self
    }

    pub async fn read_file(&self, path: &Path) -> Result<String> {
        if let Some(expectation) = self.read_expectations.first() {
            expectation.call();
        }

        self.files
            .get(path)
            .cloned()
            .ok_or_else(|| anyhow::anyhow!("File not found: {:?}", path))
    }

    pub async fn write_file(&mut self, path: &Path, content: &str) -> Result<()> {
        if let Some(expectation) = self.write_expectations.first() {
            expectation.call();
        }

        self.files.insert(path.to_path_buf(), content.to_string());
        Ok(())
    }

    pub async fn create_dir(&mut self, path: &Path) -> Result<()> {
        self.directories.push(path.to_path_buf());
        Ok(())
    }

    pub async fn exists(&self, path: &Path) -> bool {
        self.files.contains_key(path) || self.directories.iter().any(|d| d == path)
    }

    pub fn expect_read(&mut self) -> &mut Expectation {
        let expectation = Expectation::new();
        self.read_expectations.push(expectation);
        self.read_expectations.last_mut().unwrap()
    }

    pub fn expect_write(&mut self) -> &mut Expectation {
        let expectation = Expectation::new();
        self.write_expectations.push(expectation);
        self.write_expectations.last_mut().unwrap()
    }
}

impl Mock<()> for MockFileSystem {
    fn expect(&mut self) -> &mut Expectation {
        self.expect_read()
    }

    fn checkpoint(&mut self) {
        self.read_expectations.clear();
        self.write_expectations.clear();
    }

    fn verify(&self) -> Result<()> {
        for expectation in &self.read_expectations {
            expectation.verify()?;
        }
        for expectation in &self.write_expectations {
            expectation.verify()?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_mock_file_system_read() -> Result<()> {
        let fs = MockFileSystem::new()
            .with_file("/test.txt", "Hello, World!");

        let content = fs.read_file(Path::new("/test.txt")).await?;
        assert_eq!(content, "Hello, World!");

        let result = fs.read_file(Path::new("/missing.txt")).await;
        assert!(result.is_err());

        Ok(())
    }

    #[tokio::test]
    async fn test_mock_file_system_write() -> Result<()> {
        let mut fs = MockFileSystem::new();
        
        fs.write_file(Path::new("/output.txt"), "Test content").await?;
        
        let content = fs.read_file(Path::new("/output.txt")).await?;
        assert_eq!(content, "Test content");

        Ok(())
    }

    #[tokio::test]
    async fn test_mock_file_system_expectations() -> Result<()> {
        let mut fs = MockFileSystem::new()
            .with_file("/test.txt", "content");
        
        fs.expect_read().times(2);
        
        fs.read_file(Path::new("/test.txt")).await?;
        fs.read_file(Path::new("/test.txt")).await?;
        
        fs.verify()?;
        Ok(())
    }
}