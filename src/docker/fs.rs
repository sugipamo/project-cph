use std::path::{Path, PathBuf};
use crate::docker::error::DockerResult;
use std::fs;
use uuid::Uuid;

pub trait DockerFileManager {
    fn create_temp_directory(&self) -> DockerResult<PathBuf>;
    fn write_source_file(&self, dir: &Path, filename: &str, content: &str) -> DockerResult<PathBuf>;
    fn set_permissions(&self, path: &Path, mode: u32) -> DockerResult<()>;
    fn cleanup(&self, dir: &Path) -> DockerResult<()>;
}

pub struct DefaultDockerFileManager;

impl DefaultDockerFileManager {
    pub fn new() -> Self {
        Self
    }
}

impl DockerFileManager for DefaultDockerFileManager {
    fn create_temp_directory(&self) -> DockerResult<PathBuf> {
        let temp_dir = std::env::temp_dir().join(format!("cph_{}", Uuid::new_v4()));
        fs::create_dir_all(&temp_dir)?;
        Ok(temp_dir)
    }

    fn write_source_file(&self, dir: &Path, filename: &str, content: &str) -> DockerResult<PathBuf> {
        let file_path = dir.join(filename);
        fs::write(&file_path, content)?;
        Ok(file_path)
    }

    fn set_permissions(&self, path: &Path, mode: u32) -> DockerResult<()> {
        use std::os::unix::fs::PermissionsExt;
        let metadata = fs::metadata(path)?;
        let mut perms = metadata.permissions();
        perms.set_mode(mode);
        fs::set_permissions(path, perms)?;
        Ok(())
    }

    fn cleanup(&self, dir: &Path) -> DockerResult<()> {
        if dir.exists() {
            fs::remove_dir_all(dir)?;
        }
        Ok(())
    }
}

#[cfg(test)]
pub struct MockDockerFileManager {
    temp_dir: PathBuf,
}

#[cfg(test)]
impl MockDockerFileManager {
    pub fn new() -> Self {
        Self {
            temp_dir: PathBuf::from("/mock/temp/dir"),
        }
    }
}

#[cfg(test)]
impl DockerFileManager for MockDockerFileManager {
    fn create_temp_directory(&self) -> DockerResult<PathBuf> {
        Ok(self.temp_dir.clone())
    }

    fn write_source_file(&self, dir: &Path, filename: &str, _content: &str) -> DockerResult<PathBuf> {
        Ok(dir.join(filename))
    }

    fn set_permissions(&self, _path: &Path, _mode: u32) -> DockerResult<()> {
        Ok(())
    }

    fn cleanup(&self, _dir: &Path) -> DockerResult<()> {
        Ok(())
    }
} 