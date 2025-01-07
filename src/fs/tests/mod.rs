use std::path::{Path, PathBuf};
use anyhow::Result;
use tempfile::{tempdir, TempDir};

/// テスト用のヘルパー関数を提供するモジュール

pub struct TestDirectory {
    temp_dir: TempDir,
}

impl TestDirectory {
    /// 新しいテストディレクトリを作成
    pub fn new() -> Result<Self> {
        Ok(Self {
            temp_dir: tempdir()?,
        })
    }

    /// テストディレクトリのパスを取得
    pub fn path(&self) -> &Path {
        self.temp_dir.path()
    }

    /// テストファイルを作成
    pub fn create_file(&self, name: impl AsRef<Path>, content: impl AsRef<[u8]>) -> Result<PathBuf> {
        let path = self.temp_dir.path().join(name);
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::write(&path, content)?;
        Ok(path)
    }

    /// テストディレクトリを作成
    pub fn create_dir(&self, name: impl AsRef<Path>) -> Result<PathBuf> {
        let path = self.temp_dir.path().join(name);
        std::fs::create_dir_all(&path)?;
        Ok(path)
    }

    /// ファイルの内容を読み込む
    pub fn read_file(&self, name: impl AsRef<Path>) -> Result<String> {
        let path = self.temp_dir.path().join(name);
        Ok(std::fs::read_to_string(path)?)
    }

    /// パスが存在するかどうかを確認
    pub fn exists(&self, name: impl AsRef<Path>) -> bool {
        self.temp_dir.path().join(name).exists()
    }

    /// パスがファイルかどうかを確認
    pub fn is_file(&self, name: impl AsRef<Path>) -> bool {
        self.temp_dir.path().join(name).is_file()
    }

    /// パスがディレクトリかどうかを確認
    pub fn is_dir(&self, name: impl AsRef<Path>) -> bool {
        self.temp_dir.path().join(name).is_dir()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_test_directory() -> Result<()> {
        let test_dir = TestDirectory::new()?;
        
        // ファイル作成のテスト
        let file_path = test_dir.create_file("test.txt", "Hello, World!")?;
        assert!(test_dir.is_file("test.txt"));
        assert_eq!(test_dir.read_file("test.txt")?, "Hello, World!");
        
        // ディレクトリ作成のテスト
        let dir_path = test_dir.create_dir("test_dir")?;
        assert!(test_dir.is_dir("test_dir"));
        
        // ネストしたファイル作成のテスト
        let nested_file = test_dir.create_file("test_dir/nested.txt", "Nested content")?;
        assert!(test_dir.is_file("test_dir/nested.txt"));
        assert_eq!(test_dir.read_file("test_dir/nested.txt")?, "Nested content");
        
        Ok(())
    }
} 