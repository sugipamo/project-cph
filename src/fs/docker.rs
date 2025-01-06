use std::path::Path;
use std::os::unix::fs::PermissionsExt;
use crate::error::Result;
use nix::unistd::{Uid, Gid};

pub trait DockerFileOperations {
    fn create_temp_directory(&self) -> Result<std::path::PathBuf>;
    fn set_permissions<P: AsRef<Path>>(&self, path: P, mode: u32) -> Result<()>;
    fn write_source_file<P: AsRef<Path>>(&self, dir: P, filename: &str, content: &str) -> Result<std::path::PathBuf>;
}

/// Docker環境でのファイル操作のデフォルト実装
pub trait DefaultDockerFileOperations: DockerFileOperations {
    /// ディレクトリの権限を確認・設定
    fn ensure_directory_permissions(&self, dir: &Path) -> Result<()> {
        let metadata = std::fs::metadata(dir)?;
        let mut perms = metadata.permissions();
        perms.set_mode(0o777);
        std::fs::set_permissions(dir, perms)?;
        Ok(())
    }

    /// 現在のユーザーIDとグループIDを取得
    fn get_current_user_ids(&self) -> (Uid, Gid) {
        let uid = Uid::from_raw(std::process::id() as u32);
        let gid = Gid::from_raw(unsafe { libc::getgid() } as u32);
        (uid, gid)
    }
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
            if path.exists() {
                Ok(())
            } else {
                Err("Path does not exist".into())
            }
        }

        fn set_ownership(&self, path: &Path, _uid: Option<Uid>, _gid: Option<Gid>) -> Result<()> {
            if path.exists() {
                Ok(())
            } else {
                Err("Path does not exist".into())
            }
        }

        fn write_source_file<P: AsRef<Path>>(&self, dir: P, filename: &str, content: &str) -> Result<std::path::PathBuf> {
            let file_path = dir.join(filename);
            fs::write(&file_path, content)?;
            Ok(file_path)
        }
    }

    impl DefaultDockerFileOperations for MockDockerFileOps {}

    #[test]
    fn test_mock_docker_file_ops() {
        let ops = MockDockerFileOps::new();
        
        // テスト一時ディレクトリの作成
        let temp_dir = ops.create_temp_directory().unwrap();
        assert!(temp_dir.exists());

        // ソースファイルの書き込み
        let file_path = ops.write_source_file(&temp_dir, "test.txt", "test content").unwrap();
        assert!(file_path.exists());
        assert_eq!(fs::read_to_string(file_path).unwrap(), "test content");

        // 権限設定
        assert!(ops.set_permissions(&temp_dir, 0o777).is_ok());

        // 所有者設定
        let (uid, gid) = ops.get_current_user_ids();
        assert!(ops.set_ownership(&temp_dir, Some(uid), Some(gid)).is_ok());
    }
} 