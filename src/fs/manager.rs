use std::path::Path;
use crate::error::Result;
use crate::fs::error::{io_err, not_found_err};

pub struct FileManager {
    root: String,
}

impl FileManager {
    pub fn new(root: impl Into<String>) -> Self {
        Self {
            root: root.into(),
        }
    }

    pub fn read_file(&self, path: impl AsRef<Path>) -> Result<String> {
        let path = path.as_ref();
        if !path.exists() {
            return Err(not_found_err(path.to_string_lossy().to_string()));
        }
        std::fs::read_to_string(path)
            .map_err(|e| io_err(e, format!("ファイルの読み込みに失敗: {}", path.display())))
    }

    pub fn write_file(&self, path: impl AsRef<Path>, content: impl AsRef<str>) -> Result<()> {
        let path = path.as_ref();
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| io_err(e, format!("ディレクトリの作成に失敗: {}", parent.display())))?;
        }
        std::fs::write(path, content.as_ref())
            .map_err(|e| io_err(e, format!("ファイルの書き込みに失敗: {}", path.display())))
    }

    pub fn create_dir(&self, path: impl AsRef<Path>) -> Result<()> {
        let path = path.as_ref();
        if path.exists() {
            return Ok(());
        }
        std::fs::create_dir_all(path)
            .map_err(|e| io_err(e, format!("ディレクトリの作成に失敗: {}", path.display())))
    }

    pub fn remove_file(&self, path: impl AsRef<Path>) -> Result<()> {
        let path = path.as_ref();
        if !path.exists() {
            return Ok(());
        }
        std::fs::remove_file(path)
            .map_err(|e| io_err(e, format!("ファイルの削除に失敗: {}", path.display())))
    }

    pub fn remove_dir(&self, path: impl AsRef<Path>) -> Result<()> {
        let path = path.as_ref();
        if !path.exists() {
            return Ok(());
        }
        std::fs::remove_dir_all(path)
            .map_err(|e| io_err(e, format!("ディレクトリの削除に失敗: {}", path.display())))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn test_file_operations() -> Result<()> {
        let temp_dir = tempdir().unwrap();
        let manager = FileManager::new(temp_dir.path().to_string_lossy().to_string());

        // テストファイルの作成
        let test_file = temp_dir.path().join("test.txt");
        manager.write_file(&test_file, "Hello, World!")?;

        // ファイルの読み込み
        let content = manager.read_file(&test_file)?;
        assert_eq!(content, "Hello, World!");

        // ファイルの削除
        manager.remove_file(&test_file)?;
        assert!(!test_file.exists());

        // ディレクトリの作成
        let test_dir = temp_dir.path().join("test_dir");
        manager.create_dir(&test_dir)?;
        assert!(test_dir.exists());

        // ディレクトリの削除
        manager.remove_dir(&test_dir)?;
        assert!(!test_dir.exists());

        Ok(())
    }

    #[test]
    fn test_error_handling() {
        let temp_dir = tempdir().unwrap();
        let manager = FileManager::new(temp_dir.path().to_string_lossy().to_string());

        // 存在しないファイルの読み込み
        let result = manager.read_file("nonexistent.txt");
        assert!(result.is_err());

        // 権限のないディレクトリへの書き込み
        if cfg!(unix) {
            let readonly_dir = temp_dir.path().join("readonly");
            fs::create_dir(&readonly_dir).unwrap();
            fs::set_permissions(&readonly_dir, fs::Permissions::from_mode(0o444)).unwrap();

            let test_file = readonly_dir.join("test.txt");
            let result = manager.write_file(&test_file, "test");
            assert!(result.is_err());
        }
    }
} 