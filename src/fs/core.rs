use std::path::{Path, PathBuf};
use anyhow::Result;
use crate::fs::error::{not_found_error, permission_error, invalid_path_error, ErrorExt};

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

/// ファイルを読み込みます
pub fn read_file<P: AsRef<Path>>(path: P) -> Result<String> {
    let path = path.as_ref();
    if !path.exists() {
        return Err(not_found_error(path));
    }
    if !path.is_file() {
        return Err(invalid_path_error(path));
    }
    std::fs::read_to_string(path)
        .with_context_io(format!("ファイルの読み込みに失敗: {}", path.display()))
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

/// ファイルを削除します
pub fn delete_file<P: AsRef<Path>>(path: P) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Ok(());
    }
    if !path.is_file() {
        return Err(invalid_path_error(path));
    }
    std::fs::remove_file(path)
        .with_context_io(format!("ファイルの削除に失敗: {}", path.display()))
}

/// ディレクトリを削除します
pub fn delete_directory<P: AsRef<Path>>(path: P) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Ok(());
    }
    if !path.is_dir() {
        return Err(invalid_path_error(path));
    }
    std::fs::remove_dir_all(path)
        .with_context_io(format!("ディレクトリの削除に失敗: {}", path.display()))
}

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

/// パスのメタデータを取得します
pub fn metadata<P: AsRef<Path>>(path: P) -> Result<std::fs::Metadata> {
    let path = path.as_ref();
    std::fs::metadata(path)
        .with_context_io(format!("メタデータの取得に失敗: {}", path.display()))
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

    #[test]
    fn test_ensure_directory() -> Result<()> {
        let test_dir = TestDirectory::new()?;
        let dir_path = test_dir.path().join("test_dir");
        
        let result = ensure_directory(&dir_path)?;
        assert_eq!(result, dir_path);
        assert!(is_directory(&dir_path));

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
    fn test_read_write_file() -> Result<()> {
        let test_dir = TestDirectory::new()?;
        let file_path = test_dir.path().join("test.txt");
        
        write_file(&file_path, "Hello, World!")?;
        assert!(is_file(&file_path));
        
        let content = read_file(&file_path)?;
        assert_eq!(content, "Hello, World!");

        Ok(())
    }

    #[test]
    fn test_delete_operations() -> Result<()> {
        let test_dir = TestDirectory::new()?;
        let file_path = test_dir.path().join("test.txt");
        let dir_path = test_dir.path().join("test_dir");
        
        write_file(&file_path, "Hello")?;
        ensure_directory(&dir_path)?;
        
        assert!(exists(&file_path));
        assert!(exists(&dir_path));
        
        delete_file(&file_path)?;
        delete_directory(&dir_path)?;
        
        assert!(!exists(&file_path));
        assert!(!exists(&dir_path));

        Ok(())
    }

    #[test]
    fn test_metadata_and_permissions() -> Result<()> {
        let test_dir = TestDirectory::new()?;
        let file_path = test_dir.path().join("test.txt");
        
        write_file(&file_path, "Hello")?;
        
        let metadata = metadata(&file_path)?;
        assert!(metadata.is_file());
        
        check_permissions(&file_path, false)?;

        Ok(())
    }
} 