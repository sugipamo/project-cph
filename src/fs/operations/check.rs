use std::path::Path;
use anyhow::Result;
use crate::fs::error::permission_error;
use crate::fs::operations::read::metadata;

/// パスが存在するかどうかを確認します
pub fn exists<P: AsRef<Path>>(path: P) -> bool {
    path.as_ref().exists()
}

/// パスがファイルかどうかを確認します
pub fn is_file<P: AsRef<Path>>(path: P) -> bool {
    path.as_ref().is_file()
}

/// パスがディレクトリかどうかを確認します
pub fn is_directory<P: AsRef<Path>>(path: P) -> bool {
    path.as_ref().is_dir()
}

/// パスの権限を確認します
pub fn check_permissions<P: AsRef<Path>>(path: P, write_required: bool) -> Result<()> {
    let path = path.as_ref();
    let metadata = metadata(path)?;
    
    if !metadata.permissions().readonly() && write_required {
        return Err(permission_error(path));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::fs::tests::TestDirectory;
    use crate::fs::operations::write::write_file;

    #[test]
    fn test_check_operations() -> Result<()> {
        let test_dir = TestDirectory::new()?;
        let file_path = test_dir.path().join("test.txt");
        
        write_file(&file_path, "Hello")?;
        
        assert!(exists(&file_path));
        assert!(is_file(&file_path));
        assert!(!is_directory(&file_path));
        
        check_permissions(&file_path, false)?;

        Ok(())
    }
} 