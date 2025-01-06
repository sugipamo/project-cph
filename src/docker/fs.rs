use std::path::Path;
use crate::error::Result;
use crate::docker::error::docker_err;

pub trait DockerFileOperations {
    fn write_source_file<P: AsRef<Path>>(&self, dir: P, filename: &str, content: &str) -> Result<()>;
    fn set_permissions<P: AsRef<Path>>(&self, path: P, mode: u32) -> Result<()>;
}

pub struct DefaultDockerFileOperations;

impl DefaultDockerFileOperations {
    pub fn new() -> Self {
        Self
    }
}

impl DockerFileOperations for DefaultDockerFileOperations {
    fn write_source_file<P: AsRef<Path>>(&self, dir: P, filename: &str, content: &str) -> Result<()> {
        let path = dir.as_ref().join(filename);
        std::fs::write(&path, content)
            .map_err(|e| docker_err(format!("ソースファイルの書き込みに失敗しました: {}", e)))?;
        Ok(())
    }

    fn set_permissions<P: AsRef<Path>>(&self, path: P, mode: u32) -> Result<()> {
        use std::os::unix::fs::PermissionsExt;
        let path = path.as_ref();
        let metadata = std::fs::metadata(path)
            .map_err(|e| docker_err(format!("メタデータの取得に失敗しました: {}", e)))?;
        let mut perms = metadata.permissions();
        perms.set_mode(mode);
        std::fs::set_permissions(path, perms)
            .map_err(|e| docker_err(format!("権限の設定に失敗しました: {}", e)))?;
        Ok(())
    }
} 