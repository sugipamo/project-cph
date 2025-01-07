use std::path::{Path, PathBuf};
use crate::error::Result;
use super::error::{
    create_not_found_error,
    create_io_error,
    create_invalid_path_error,
    create_permission_error,
};

/// ディレクトリの存在を確認し、存在しない場合は作成します
pub fn ensure_directory<P: AsRef<Path>>(path: P) -> Result<PathBuf> {
    let path = path.as_ref();
    if !path.exists() {
        std::fs::create_dir_all(path)
            .map_err(|e| create_io_error(e, format!("ディレクトリの作成に失敗: {}", path.display())))?;
    } else if !path.is_dir() {
        return Err(create_invalid_path_error(path));
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
            .map_err(|e| create_io_error(e, format!("ファイルの作成に失敗: {}", path.display())))?;
    } else if !path.is_file() {
        return Err(create_invalid_path_error(path));
    }
    Ok(path.to_path_buf())
}

/// ファイルを読み込みます
pub fn read_file<P: AsRef<Path>>(path: P) -> Result<String> {
    let path = path.as_ref();
    if !path.exists() {
        return Err(create_not_found_error(path));
    }
    if !path.is_file() {
        return Err(create_invalid_path_error(path));
    }
    std::fs::read_to_string(path)
        .map_err(|e| create_io_error(e, format!("ファイルの読み込みに失敗: {}", path.display())))
}

/// ファイルに書き込みます
pub fn write_file<P: AsRef<Path>>(path: P, content: impl AsRef<[u8]>) -> Result<()> {
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        ensure_directory(parent)?;
    }
    std::fs::write(path, content)
        .map_err(|e| create_io_error(e, format!("ファイルの書き込みに失敗: {}", path.display())))
}

/// ファイルを削除します
pub fn delete_file<P: AsRef<Path>>(path: P) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Ok(());
    }
    if !path.is_file() {
        return Err(create_invalid_path_error(path));
    }
    std::fs::remove_file(path)
        .map_err(|e| create_io_error(e, format!("ファイルの削除に失敗: {}", path.display())))
}

/// ディレクトリを削除します
pub fn delete_directory<P: AsRef<Path>>(path: P) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        return Ok(());
    }
    if !path.is_dir() {
        return Err(create_invalid_path_error(path));
    }
    std::fs::remove_dir_all(path)
        .map_err(|e| create_io_error(e, format!("ディレクトリの削除に失敗: {}", path.display())))
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
        .map_err(|e| create_io_error(e, format!("メタデータの取得に失敗: {}", path.display())))
}

/// パスの権限を確認します
pub fn check_permissions<P: AsRef<Path>>(path: P, write_required: bool) -> Result<()> {
    let path = path.as_ref();
    let metadata = metadata(path)?;
    
    if !metadata.permissions().readonly() && write_required {
        return Err(create_permission_error(path));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_ensure_directory() -> Result<()> {
        let temp = tempdir()?;
        let dir_path = temp.path().join("test_dir");
        
        let result = ensure_directory(&dir_path)?;
        assert_eq!(result, dir_path);
        assert!(is_directory(&dir_path));

        Ok(())
    }

    #[test]
    fn test_ensure_file() -> Result<()> {
        let temp = tempdir()?;
        let file_path = temp.path().join("test.txt");
        
        let result = ensure_file(&file_path)?;
        assert_eq!(result, file_path);
        assert!(is_file(&file_path));

        Ok(())
    }

    #[test]
    fn test_read_write_file() -> Result<()> {
        let temp = tempdir()?;
        let file_path = temp.path().join("test.txt");
        
        write_file(&file_path, "Hello, World!")?;
        assert!(is_file(&file_path));
        
        let content = read_file(&file_path)?;
        assert_eq!(content, "Hello, World!");

        Ok(())
    }

    #[test]
    fn test_delete_operations() -> Result<()> {
        let temp = tempdir()?;
        let file_path = temp.path().join("test.txt");
        let dir_path = temp.path().join("test_dir");
        
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
        let temp = tempdir()?;
        let file_path = temp.path().join("test.txt");
        
        write_file(&file_path, "Hello")?;
        
        let metadata = metadata(&file_path)?;
        assert!(metadata.is_file());
        
        check_permissions(&file_path, false)?;

        Ok(())
    }
} 