use std::fs::File;
use std::io::Write;
use anyhow::Result;
use tempfile::TempDir;

#[allow(dead_code)]
pub struct TestHelper {
    temp_dir: TempDir,
}

#[allow(dead_code)]
impl TestHelper {
    pub fn new() -> Result<Self> {
        let temp_dir = TempDir::new()?;
        Ok(Self { temp_dir })
    }

    pub fn create_file(&self, name: &str, content: &str) -> Result<()> {
        let path = self.temp_dir.path().join(name);
        let mut file = File::create(path)?;
        file.write_all(content.as_bytes())?;
        Ok(())
    }

    pub fn path(&self) -> &std::path::Path {
        self.temp_dir.path()
    }
} 