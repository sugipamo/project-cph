use std::path::{Path, PathBuf};
use anyhow::Result;
use crate::fs::error::{invalid_path_error, ErrorExt};

/// ディレクトリの存在を確認し、存在しない場合は作成します
pub fn ensure_directory<P: AsRef<Path>>(path: P) -> Result<PathBuf> {
    let path = path.as_ref();
    if !path.exists() {
        std::fs::create_dir_all(path)
            .with_context_io(format!("ディレクトリの作成に失敗: {}", path.display()))?;
    } else if !path.is_dir() {
        return Err(invalid_path_error(path));
    }
    Ok(path.to_path_buf())
}

/// ファイルの存在を確認し、存在しない場合は作成します
pub fn ensure_file<P: AsRef<Path>>(path: P) -> Result<PathBuf> {
    let path = path.as_ref();
    if !path.exists() {
        if let Some(parent) = path.parent() {
            ensure_directory(parent)?;
        }
        std::fs::write(path, "")
            .with_context_io(format!("ファイルの作成に失敗: {}", path.display()))?;
    } else if !path.is_file() {
        return Err(invalid_path_error(path));
    }
    Ok(path.to_path_buf())
}

/// ファイルに書き込みます
pub fn write_file<P: AsRef<Path>>(path: P, content: impl AsRef<[u8]>) -> Result<()> {
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        ensure_directory(parent)?;
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