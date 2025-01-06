use std::path::Path;
use std::os::unix::fs::PermissionsExt;
use crate::error::{CphError, FileSystemError, Result};
use nix::unistd::{Uid, Gid};

#[allow(dead_code)]
pub trait DockerFileOperations {
    fn create_temp_directory(&self) -> Result<std::path::PathBuf>;
    fn set_permissions<P: AsRef<Path>>(&self, path: P, mode: u32) -> Result<()>;
    fn write_source_file<P: AsRef<Path>>(&self, dir: P, filename: &str, content: &str) -> Result<std::path::PathBuf>;
}

#[allow(dead_code)]
pub trait DefaultDockerFileOperations: DockerFileOperations {
    fn ensure_directory_permissions(&self, dir: &Path) -> Result<()> {
        let metadata = std::fs::metadata(dir)
            .map_err(|e| CphError::Fs(FileSystemError::Io(e, "Dockerファイルシステムの操作中のエラー".to_string())))?;
        let mut perms = metadata.permissions();
        perms.set_mode(0o777);
        std::fs::set_permissions(dir, perms)
            .map_err(|e| CphError::Fs(FileSystemError::Io(e, "Dockerファイルシステムの操作中のエラー".to_string())))?;
        Ok(())
    }

    fn get_current_user_ids(&self) -> (Uid, Gid) {
        let uid = Uid::from_raw(std::process::id() as u32);
        let gid = Gid::from_raw(unsafe { libc::getgid() } as u32);
        (uid, gid)
    }
}

pub fn set_docker_dir_permissions<P: AsRef<Path>>(dir: P) -> Result<()> {
    let dir = dir.as_ref();

    let metadata = std::fs::metadata(dir)
        .map_err(|e| CphError::Fs(FileSystemError::Io(e, "Dockerファイルシステムの操作中のエラー".to_string())))?;

    let mut perms = metadata.permissions();
    perms.set_mode(0o777);
    std::fs::set_permissions(dir, perms)
        .map_err(|e| CphError::Fs(FileSystemError::Io(e, "Dockerファイルシステムの操作中のエラー".to_string())))?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use std::fs;

    struct MockDockerFileOps {
        temp_dir: TempDir,
    }

    impl MockDockerFileOps {
        fn new() -> Self {
            Self {
                temp_dir: TempDir::new().unwrap(),
            }
        }
    }

    impl DockerFileOperations for MockDockerFileOps {
        fn create_temp_directory(&self) -> Result<std::path::PathBuf> {
            Ok(self.temp_dir.path().to_path_buf())
        }

        fn set_permissions<P: AsRef<Path>>(&self, path: P, _mode: u32) -> Result<()> {
            if path.as_ref().exists() {
                Ok(())
            } else {
                Err(CphError::Fs(FileSystemError::NotFound {
                    path: path.as_ref().to_string_lossy().to_string()
                }))
            }
        }

        fn write_source_file<P: AsRef<Path>>(&self, dir: P, filename: &str, content: &str) -> Result<std::path::PathBuf> {
            let file_path = dir.as_ref().join(filename);
            fs::write(&file_path, content)
                .map_err(|e| CphError::Fs(FileSystemError::Io(e, "Dockerファイルシステムの操作中のエラー".to_string())))?;
            Ok(file_path)
        }
    }

    impl DefaultDockerFileOperations for MockDockerFileOps {}

    #[test]
    fn test_mock_docker_file_ops() -> Result<()> {
        let ops = MockDockerFileOps::new();
        
        // テスト一時ディレクトリの作成
        let temp_dir = ops.create_temp_directory()?;
        assert!(temp_dir.exists());

        // ソースファイルの書き込み
        let file_path = ops.write_source_file(&temp_dir, "test.txt", "test content")?;
        assert!(file_path.exists());
        assert_eq!(fs::read_to_string(&file_path)
            .map_err(|e| CphError::Fs(FileSystemError::Io(e, "Dockerファイルシステムの操作中のエラー".to_string())))?, "test content");

        // 権限設定
        ops.set_permissions(&temp_dir, 0o777)?;

        Ok(())
    }

    #[test]
    fn test_set_docker_dir_permissions() -> Result<()> {
        let temp_dir = TempDir::new()
            .map_err(|e| CphError::Fs(FileSystemError::Io(e, "Dockerファイルシステムの操作中のエラー".to_string())))?;

        set_docker_dir_permissions(temp_dir.path())?;

        let metadata = fs::metadata(temp_dir.path())
            .map_err(|e| CphError::Fs(FileSystemError::Io(e, "Dockerファイルシステムの操作中のエラー".to_string())))?;
        let mode = metadata.permissions().mode();
        assert_eq!(mode & 0o777, 0o777);

        Ok(())
    }
} 