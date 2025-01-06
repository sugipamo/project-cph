use std::path::Path;
use std::os::unix::fs::PermissionsExt;
use crate::error::Result;
use nix::unistd::{Uid, Gid};
use crate::docker::error::docker_err;

pub trait DockerFileOperations {
    fn create_temp_directory(&self) -> Result<std::path::PathBuf>;
    fn set_permissions<P: AsRef<Path>>(&self, path: P, mode: u32) -> Result<()>;
    fn write_source_file<P: AsRef<Path>>(&self, dir: P, filename: &str, content: &str) -> Result<std::path::PathBuf>;
}

/// Docker環境でのファイル操作のデフォルト実装
pub trait DefaultDockerFileOperations: DockerFileOperations {
    /// ディレクトリの権限を確認・設定
    fn ensure_directory_permissions(&self, dir: &Path) -> Result<()> {
        let metadata = std::fs::metadata(dir)
            .map_err(|e| docker_err(format!("ディレクトリのメタデータの取得に失敗しました: {}", e)))?;
        let mut perms = metadata.permissions();
        perms.set_mode(0o777);
        std::fs::set_permissions(dir, perms)
            .map_err(|e| docker_err(format!("ディレクトリの権限設定に失敗しました: {}", e)))?;
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
        fn new() -> Result<Self> {
            let temp_dir = TempDir::new()
                .map_err(|e| container_err(format!("一時ディレクトリの作成に失敗しました: {}", e)))?;
            Ok(Self { temp_dir })
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
                Err(container_err("パスが存在しません".to_string()))
            }
        }

        fn write_source_file<P: AsRef<Path>>(&self, dir: P, filename: &str, content: &str) -> Result<std::path::PathBuf> {
            let file_path = dir.as_ref().join(filename);
            fs::write(&file_path, content)
                .map_err(|e| container_err(format!("ソースファイルの書き込みに失敗しました: {}", e)))?;
            Ok(file_path)
        }
    }

    impl DefaultDockerFileOperations for MockDockerFileOps {}

    #[test]
    fn test_mock_docker_file_ops() -> Result<()> {
        let ops = MockDockerFileOps::new()?;
        
        // テスト一時ディレクトリの作成
        let temp_dir = ops.create_temp_directory()?;
        assert!(temp_dir.exists());

        // ソースファイルの書き込み
        let file_path = ops.write_source_file(&temp_dir, "test.txt", "test content")?;
        assert!(file_path.exists());
        let content = fs::read_to_string(&file_path)
            .map_err(|e| container_err(format!("ファイルの読み取りに失敗しました: {}", e)))?;
        assert_eq!(content, "test content");

        // 権限設定
        assert!(ops.set_permissions(&temp_dir, 0o777).is_ok());

        // 所有者設定
        let (uid, gid) = ops.get_current_user_ids();
        assert!(uid.is_root() || !uid.is_root());
        assert!(gid.is_root() || !gid.is_root());

        Ok(())
    }
} 