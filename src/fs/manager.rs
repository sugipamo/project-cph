use std::path::{Path, PathBuf};
use std::sync::Arc;
use crate::error::Result;
use crate::fs::error::{io_err, not_found_err, invalid_path_err};

#[derive(Debug, Clone)]
pub struct FileManager {
    root: Arc<PathBuf>,
}

impl FileManager {
    pub fn new(root: impl Into<PathBuf>) -> Self {
        Self {
            root: Arc::new(root.into()),
        }
    }

    // パスの正規化と検証を行うヘルパーメソッド
    fn normalize_path(&self, path: impl AsRef<Path>) -> Result<PathBuf> {
        let path = path.as_ref();
        
        // 絶対パスの場合はエラー
        if path.is_absolute() {
            return Err(invalid_path_err(format!(
                "絶対パスは使用できません: {}",
                path.display()
            )));
        }

        // パスのトラバーサルを防ぐ
        let normalized = path.components()
            .fold(Ok(PathBuf::new()), |acc, component| {
                let mut path = acc?;
                match component {
                    std::path::Component::ParentDir => {
                        if path.pop() {
                            Ok(path)
                        } else {
                            Err(invalid_path_err(format!(
                                "パスが親ディレクトリを超えて遡ることはできません: {}",
                                path.display()
                            )))
                        }
                    },
                    std::path::Component::Normal(name) => {
                        path.push(name);
                        Ok(path)
                    },
                    _ => Ok(path),
                }
            })?;

        Ok(self.root.join(normalized))
    }

    pub fn read_file(&self, path: impl AsRef<Path>) -> Result<String> {
        let path = self.normalize_path(path)?;
        if !path.exists() {
            return Err(not_found_err(format!(
                "ファイルが見つかりません: {}",
                path.display()
            )));
        }
        std::fs::read_to_string(&path)
            .map_err(|e| io_err(e, format!("ファイルの読み込みに失敗: {}", path.display())))
    }

    pub fn write_file(&self, path: impl AsRef<Path>, content: impl AsRef<str>) -> Result<()> {
        let path = self.normalize_path(path)?;
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| io_err(e, format!("ディレクトリの作成に失敗: {}", parent.display())))?;
        }
        std::fs::write(&path, content.as_ref())
            .map_err(|e| io_err(e, format!("ファイルの書き込みに失敗: {}", path.display())))
    }

    pub fn delete_file(&self, path: impl AsRef<Path>) -> Result<()> {
        let path = self.normalize_path(path)?;
        if !path.exists() {
            return Ok(());
        }
        std::fs::remove_file(&path)
            .map_err(|e| io_err(e, format!("ファイルの削除に失敗: {}", path.display())))
    }

    pub fn create_dir(&self, path: impl AsRef<Path>) -> Result<()> {
        let path = self.normalize_path(path)?;
        std::fs::create_dir_all(&path)
            .map_err(|e| io_err(e, format!("ディレクトリの作成に失敗: {}", path.display())))
    }

    pub fn exists(&self, path: impl AsRef<Path>) -> Result<bool> {
        let path = self.normalize_path(path)?;
        Ok(path.exists())
    }

    pub fn root_path(&self) -> &Path {
        self.root.as_ref()
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
        manager.delete_file(&test_file)?;
        assert!(!test_file.exists());

        // ディレクトリの作成
        let test_dir = temp_dir.path().join("test_dir");
        manager.create_dir(&test_dir)?;
        assert!(test_dir.exists());

        // ディレクトリの削除
        manager.delete_file(&test_dir)?;
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