pub mod mock_drivers;

use anyhow::Result;
use std::collections::HashMap;
use std::path::PathBuf;
use tempfile::TempDir;

#[derive(Debug)]
pub struct TestConfig {
    pub temp_dir: Option<TempDir>,
    pub env_vars: HashMap<String, String>,
}

impl Default for TestConfig {
    fn default() -> Self {
        Self {
            temp_dir: None,
            env_vars: HashMap::new(),
        }
    }
}

pub struct TestFixture {
    temp_dir: TempDir,
    config: TestConfig,
    files: HashMap<PathBuf, String>,
}

impl TestFixture {
    pub fn new() -> Result<Self> {
        let temp_dir = TempDir::new()?;
        Ok(Self {
            temp_dir,
            config: TestConfig::default(),
            files: HashMap::new(),
        })
    }

    pub fn with_file(mut self, path: &str, content: &str) -> Self {
        let full_path = self.temp_dir.path().join(path);
        self.files.insert(full_path, content.to_string());
        self
    }

    pub fn with_env(mut self, key: &str, value: &str) -> Self {
        self.config.env_vars.insert(key.to_string(), value.to_string());
        self
    }

    pub fn build(self) -> Result<TestContext> {
        for (path, content) in &self.files {
            if let Some(parent) = path.parent() {
                std::fs::create_dir_all(parent)?;
            }
            std::fs::write(path, content)?;
        }

        Ok(TestContext {
            temp_dir: self.temp_dir,
            config: self.config,
        })
    }
}

pub struct TestContext {
    pub temp_dir: TempDir,
    pub config: TestConfig,
}

impl TestContext {
    pub fn path(&self) -> &std::path::Path {
        self.temp_dir.path()
    }
}

#[derive(Debug, Clone)]
pub struct Expectation {
    pub times: Option<usize>,
    pub called: std::sync::Arc<std::sync::Mutex<usize>>,
}

impl Expectation {
    pub fn new() -> Self {
        Self {
            times: None,
            called: std::sync::Arc::new(std::sync::Mutex::new(0)),
        }
    }

    pub fn times(&mut self, n: usize) -> &mut Self {
        self.times = Some(n);
        self
    }

    pub fn verify(&self) -> Result<()> {
        let called = *self.called.lock().unwrap();
        if let Some(expected) = self.times {
            if called != expected {
                anyhow::bail!(
                    "Expected to be called {} times, but was called {} times",
                    expected,
                    called
                );
            }
        }
        Ok(())
    }

    pub fn call(&self) {
        let mut called = self.called.lock().unwrap();
        *called += 1;
    }
}

pub trait Mock<T> {
    fn expect(&mut self) -> &mut Expectation;
    fn checkpoint(&mut self);
    fn verify(&self) -> Result<()>;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fixture_creates_files() -> Result<()> {
        let context = TestFixture::new()?
            .with_file("test.txt", "Hello, World!")
            .with_file("dir/nested.txt", "Nested content")
            .build()?;

        let test_file = context.path().join("test.txt");
        assert!(test_file.exists());
        assert_eq!(std::fs::read_to_string(test_file)?, "Hello, World!");

        let nested_file = context.path().join("dir/nested.txt");
        assert!(nested_file.exists());
        assert_eq!(std::fs::read_to_string(nested_file)?, "Nested content");

        Ok(())
    }

    #[test]
    fn test_expectation_verification() -> Result<()> {
        let mut binding = Expectation::new();
        let expectation = binding.times(2);
        
        expectation.call();
        expectation.call();
        
        expectation.verify()?;
        Ok(())
    }

    #[test]
    fn test_expectation_verification_fails() {
        let mut binding = Expectation::new();
        let expectation = binding.times(2);
        
        expectation.call();
        
        assert!(expectation.verify().is_err());
    }
}