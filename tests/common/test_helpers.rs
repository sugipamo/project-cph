use std::path::PathBuf;
use tempfile::TempDir;
use anyhow::Result;

pub struct TestEnvironment {
    _temp_dir: TempDir,
    pub work_dir: PathBuf,
}

impl TestEnvironment {
    pub fn new() -> Result<Self> {
        let temp_dir = TempDir::new()?;
        let work_dir = temp_dir.path().join("workspace");
        std::fs::create_dir_all(&work_dir)?;
        
        Ok(Self {
            _temp_dir: temp_dir,
            work_dir,
        })
    }

    pub fn create_file(&self, relative_path: &str, content: &str) -> Result<PathBuf> {
        let file_path = self.work_dir.join(relative_path);
        if let Some(parent) = file_path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::write(&file_path, content)?;
        Ok(file_path)
    }

    pub fn read_file(&self, relative_path: &str) -> Result<String> {
        let file_path = self.work_dir.join(relative_path);
        Ok(std::fs::read_to_string(file_path)?)
    }

    pub fn file_exists(&self, relative_path: &str) -> bool {
        self.work_dir.join(relative_path).exists()
    }

    #[allow(dead_code)]
    pub fn path(&self) -> &std::path::Path {
        &self.work_dir
    }
}