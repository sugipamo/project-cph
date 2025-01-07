use std::path::{Path, PathBuf};
use anyhow::Result;
use crate::fs::error::{invalid_path_error, ErrorExt};

/// パス操作に関する共通機能を提供するモジュール

/// パスの正規化と検証を行う
pub fn normalize_path(root: impl AsRef<Path>, path: impl AsRef<Path>) -> Result<PathBuf> {
    let path = path.as_ref();
    
    // 絶対パスの場合はエラー
    if path.is_absolute() {
        return Err(invalid_path_error(path));
    }

    // パスのトラバーサルを防ぐ
    let normalized = path.components()
        .try_fold(Vec::new(), |mut components, component| {
            match component {
                std::path::Component::ParentDir => {
                    if components.is_empty() {
                        Err(invalid_path_error(path))
                    } else {
                        components.pop();
                        Ok(components)
                    }
                },
                std::path::Component::Normal(name) => {
                    components.push(name.to_owned());
                    Ok(components)
                },
                _ => Ok(components),
            }
        })?;

    // コンポーネントからパスを構築
    let path = normalized.iter()
        .fold(PathBuf::new(), |mut path, component| {
            path.push(component);
            path
        });

    Ok(root.as_ref().join(path))
}

/// パスが安全かどうかを検証する
pub fn validate_path(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();

    // 絶対パスの検証
    if path.is_absolute() {
        return Err(invalid_path_error(path));
    }

    // パスコンポーネントの検証
    for component in path.components() {
        match component {
            std::path::Component::ParentDir => {
                return Err(invalid_path_error(path));
            },
            std::path::Component::RootDir => {
                return Err(invalid_path_error(path));
            },
            _ => continue,
        }
    }

    Ok(())
}

/// パスの存在を確認する
pub fn ensure_path_exists(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if !path.exists() {
        std::fs::create_dir_all(path)
            .with_context_io(format!("ディレクトリの作成に失敗: {}", path.display()))?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_normalize_path() -> Result<()> {
        let root = PathBuf::from("/root");
        
        // 通常のパス
        let result = normalize_path(&root, "test/path")?;
        assert_eq!(result, PathBuf::from("/root/test/path"));
        
        // 親ディレクトリへの参照を含むパス
        let result = normalize_path(&root, "test/../path")?;
        assert_eq!(result, PathBuf::from("/root/path"));
        
        // 絶対パス（エラーになるべき）
        assert!(normalize_path(&root, "/absolute/path").is_err());
        
        // 不正なパストラバーサル（エラーになるべき）
        assert!(normalize_path(&root, "../../etc/passwd").is_err());
        
        Ok(())
    }

    #[test]
    fn test_validate_path() -> Result<()> {
        // 通常のパス
        assert!(validate_path("test/path").is_ok());
        
        // 絶対パス
        assert!(validate_path("/absolute/path").is_err());
        
        // 不正なパストラバーサル
        assert!(validate_path("../../etc/passwd").is_err());
        
        Ok(())
    }

    #[test]
    fn test_ensure_path_exists() -> Result<()> {
        let temp = tempdir()?;
        let test_path = temp.path().join("test/path");
        
        ensure_path_exists(&test_path)?;
        assert!(test_path.exists());
        
        Ok(())
    }
} 