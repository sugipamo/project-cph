use std::fs;
use std::path::{Path, PathBuf};
use std::os::unix::fs::PermissionsExt;
use tempfile::TempDir;
use crate::docker::error::{DockerError, DockerResult};
use nix::unistd::{Uid, Gid};

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

    fn ensure_directory_permissions(&self, dir: &Path) -> DockerResult<()> {
        let metadata = fs::metadata(dir)?;
        let mut perms = metadata.permissions();
        perms.set_mode(0o777);
        fs::set_permissions(dir, perms)?;
        Ok(())
    }
}

impl DockerFileManager for DefaultDockerFileManager {
    fn create_temp_directory(&self) -> DockerResult<PathBuf> {
        let temp_dir = TempDir::new()
            .map_err(|e| DockerError::Filesystem(format!("一時ディレクトリの作成に失敗しました: {}", e)))?;
        
        let temp_path = temp_dir.path().to_path_buf();
        self.ensure_directory_permissions(&temp_path)?;

        // 所有者とグループを現在のユーザーに設定
        let uid = Uid::from_raw(std::process::id() as u32);
        let gid = Gid::from_raw(unsafe { libc::getgid() } as u32);
        
        nix::unistd::chown(&temp_path, Some(uid), Some(gid))?;

        println!("=== Temporary Directory Created ===");
        println!("Path: {:?}", temp_path);
        println!("Permissions: {:o}", fs::metadata(&temp_path)?.permissions().mode());
        println!("Owner: {}:{}", uid, gid);

        Ok(temp_path)
    }

    fn write_source_file(&self, dir: &Path, filename: &str, content: &str) -> DockerResult<PathBuf> {
        let file_path = dir.join(filename);
        fs::write(&file_path, content)?;

        // 所有者とグループを現在のユーザーに設定
        let uid = Uid::from_raw(std::process::id() as u32);
        let gid = Gid::from_raw(unsafe { libc::getgid() } as u32);
        
        nix::unistd::chown(&file_path, Some(uid), Some(gid))?;

        println!("=== Source File Created ===");
        println!("Path: {:?}", file_path);
        println!("Permissions: {:o}", fs::metadata(&file_path)?.permissions().mode());
        println!("Owner: {}:{}", uid, gid);

        Ok(file_path)
    }

    fn set_permissions(&self, path: &Path, mode: u32) -> DockerResult<()> {
        let metadata = fs::metadata(path)?;
        let mut perms = metadata.permissions();
        perms.set_mode(mode);
        fs::set_permissions(path, perms)?;

        println!("=== Permissions Set ===");
        println!("Path: {:?}", path);
        println!("Mode: {:o}", mode);

        Ok(())
    }

    fn cleanup(&self, dir: &Path) -> DockerResult<()> {
        if dir.exists() {
            fs::remove_dir_all(dir)?;
        }
        Ok(())
    }
}

#[cfg(any(test, feature = "testing"))]
pub struct MockDockerFileManager {
    temp_dir: TempDir,
    should_fail: bool,
}

#[cfg(any(test, feature = "testing"))]
impl MockDockerFileManager {
    pub fn new() -> Self {
        Self {
            temp_dir: TempDir::new().unwrap(),
            should_fail: false,
        }
    }

    pub fn set_should_fail(&mut self, should_fail: bool) {
        self.should_fail = should_fail;
    }
}

#[cfg(any(test, feature = "testing"))]
impl DockerFileManager for MockDockerFileManager {
    fn create_temp_directory(&self) -> DockerResult<PathBuf> {
        if self.should_fail {
            return Err(DockerError::Filesystem("モックエラー".to_string()));
        }
        Ok(self.temp_dir.path().to_path_buf())
    }

    fn write_source_file(&self, dir: &Path, filename: &str, content: &str) -> DockerResult<PathBuf> {
        if self.should_fail {
            return Err(DockerError::Filesystem("モックエラー".to_string()));
        }
        let file_path = dir.join(filename);
        fs::write(&file_path, content)?;
        Ok(file_path)
    }

    fn set_permissions(&self, path: &Path, _mode: u32) -> DockerResult<()> {
        if self.should_fail {
            return Err(DockerError::Filesystem("モックエラー".to_string()));
        }
        if path.exists() {
            Ok(())
        } else {
            Err(DockerError::Filesystem(format!("Path does not exist: {:?}", path)))
        }
    }

    fn cleanup(&self, _dir: &Path) -> DockerResult<()> {
        if self.should_fail {
            return Err(DockerError::Filesystem("モックエラー".to_string()));
        }
        Ok(())
    }
} 