use crate::fs::error::{invalid_path_error, ErrorExt};
use anyhow::Result;
use std::path::Path;

pub fn create_dir(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if path.exists() {
        if path.is_dir() {
            return Ok(());
        }
        return Err(invalid_path_error(path));
    }
    std::fs::create_dir_all(path)
        .with_context_io(format!("ディレクトリの作成に失敗: {}", path.display()))?;
    Ok(())
}

pub fn create_file(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if path.exists() {
        if path.is_file() {
            return Ok(());
        }
        return Err(invalid_path_error(path));
    }
    if let Some(parent) = path.parent() {
        create_dir(parent)?;
    }
    std::fs::write(path, "")
        .with_context_io(format!("ファイルの作成に失敗: {}", path.display()))?;
    Ok(())
}

pub fn write_file(path: impl AsRef<Path>, content: impl AsRef<[u8]>) -> Result<()> {
    let path = path.as_ref();
    if path.exists() && !path.is_file() {
        return Err(invalid_path_error(path));
    }
    if let Some(parent) = path.parent() {
        create_dir(parent)?;
    }
    std::fs::write(path, content)
        .with_context_io(format!("ファイルの書き込みに失敗: {}", path.display()))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::fs::tests::TestDirectory;
    use crate::fs::operations::check::is_file;

    #[test]
    fn test_ensure_directory() -> Result<()> {
        let test_dir = TestDirectory::new()?;
        let dir_path = test_dir.path().join("test_dir");
        
        let result = ensure_directory(&dir_path)?;
        assert_eq!(result, dir_path);
        assert!(dir_path.is_dir());

        Ok(())
    }

    #[test]
    fn test_ensure_file() -> Result<()> {
        let test_dir = TestDirectory::new()?;
        let file_path = test_dir.path().join("test.txt");
        
        let result = ensure_file(&file_path)?;
        assert_eq!(result, file_path);
        assert!(is_file(&file_path));

        Ok(())
    }

    #[test]
    fn test_write_file() -> Result<()> {
        let test_dir = TestDirectory::new()?;
        let file_path = test_dir.path().join("test.txt");
        
        write_file(&file_path, "Hello, World!")?;
        assert!(is_file(&file_path));
        assert_eq!(std::fs::read_to_string(&file_path)?, "Hello, World!");

        Ok(())
    }
} 