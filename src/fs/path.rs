use std::path::{Path, PathBuf};
use anyhow::Result;
use crate::fs::error::{invalid_path_error, ErrorExt};

/// パスの検証レベルを定義する列挙型
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PathValidationLevel {
    /// 基本的な検証のみ（絶対パスとパストラバーサルのチェック）
    Basic,
    /// 厳格な検証（Basic + 特殊文字、非ASCII文字、長さ制限など）
    Strict,
}

/// パス操作に関する共通機能を提供するモジュール
pub struct PathValidator {
    /// パスの検証レベル
    validation_level: PathValidationLevel,
    /// パス長の最大値（バイト単位）
    max_path_length: usize,
    /// ファイル名の最大長（バイト単位）
    max_filename_length: usize,
}

impl Default for PathValidator {
    fn default() -> Self {
        Self {
            validation_level: PathValidationLevel::Basic,
            max_path_length: 4096,
            max_filename_length: 255,
        }
    }
}

impl PathValidator {
    /// 新しいPathValidatorを作成
    pub fn new(
        validation_level: PathValidationLevel,
        max_path_length: usize,
        max_filename_length: usize,
    ) -> Self {
        Self {
            validation_level,
            max_path_length,
            max_filename_length,
        }
    }

    /// パスを検証
    pub fn validate(&self, path: impl AsRef<Path>) -> Result<()> {
        let path = path.as_ref();

        // 基本的な検証
        if path.is_absolute() {
            return Err(invalid_path_error(path));
        }

        let path_str = path.to_string_lossy();
        if path_str.len() > self.max_path_length {
            return Err(invalid_path_error(format!("パスが長すぎます（最大{}バイト）", self.max_path_length)));
        }

        // パスコンポーネントの検証
        for component in path.components() {
            match component {
                std::path::Component::ParentDir => {
                    return Err(invalid_path_error("パストラバーサルは許可されていません"));
                }
                std::path::Component::RootDir => {
                    return Err(invalid_path_error("絶対パスは許可されていません"));
                }
                std::path::Component::Normal(name) => {
                    let name_str = name.to_string_lossy();
                    if name_str.len() > self.max_filename_length {
                        return Err(invalid_path_error(
                            format!("ファイル名が長すぎます（最大{}バイト）", self.max_filename_length)
                        ));
                    }

                    if self.validation_level == PathValidationLevel::Strict {
                        // 特殊文字のチェック
                        if name_str.contains(|c: char| {
                            c.is_control() || c == '<' || c == '>' || c == ':' || c == '"' ||
                            c == '/' || c == '\\' || c == '|' || c == '?' || c == '*'
                        }) {
                            return Err(invalid_path_error("ファイル名に無効な文字が含まれています"));
                        }

                        // 非ASCII文字のチェック（必要に応じて）
                        if !name_str.chars().all(|c| c.is_ascii()) {
                            return Err(invalid_path_error("ファイル名に非ASCII文字が含まれています"));
                        }
                    }
                }
                _ => continue,
            }
        }

        Ok(())
    }

    /// パスを正規化
    pub fn normalize(&self, root: impl AsRef<Path>, path: impl AsRef<Path>) -> Result<PathBuf> {
        let path = path.as_ref();
        
        // パスの検証
        self.validate(path)?;

        // パスの正規化
        let normalized = path.components()
            .filter(|c| matches!(c, std::path::Component::Normal(_)))
            .fold(PathBuf::new(), |mut result, component| {
                result.push(component);
                result
            });

        Ok(root.as_ref().join(normalized))
    }
}

/// パスの正規化と検証を行う（デフォルトの設定を使用）
pub fn normalize_path(root: impl AsRef<Path>, path: impl AsRef<Path>) -> Result<PathBuf> {
    PathValidator::default().normalize(root, path)
}

/// パスが安全かどうかを検証する（デフォルトの設定を使用）
pub fn validate_path(path: impl AsRef<Path>) -> Result<()> {
    PathValidator::default().validate(path)
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
    fn test_path_validation() {
        let validator = PathValidator::default();

        // 基本的な検証
        assert!(validator.validate("normal/path").is_ok());
        assert!(validator.validate("/absolute/path").is_err());
        assert!(validator.validate("../parent/path").is_err());
        
        // パス長の検証
        let long_path = "a".repeat(5000);
        assert!(validator.validate(long_path).is_err());

        // 厳格な検証
        let strict_validator = PathValidator::new(
            PathValidationLevel::Strict,
            4096,
            255,
        );
        assert!(strict_validator.validate("normal-path_123.txt").is_ok());
        assert!(strict_validator.validate("path/with/*/wildcard").is_err());
        assert!(strict_validator.validate("path/with/<invalid>").is_err());
        assert!(strict_validator.validate("path/with/日本語").is_err());
    }

    #[test]
    fn test_path_normalization() {
        let validator = PathValidator::default();
        let temp_dir = tempdir().unwrap();

        // 正常なパスの正規化
        let normalized = validator.normalize(&temp_dir.path(), "normal/path").unwrap();
        assert_eq!(
            normalized,
            temp_dir.path().join("normal").join("path")
        );

        // 不正なパスの正規化
        assert!(validator.normalize(&temp_dir.path(), "/absolute/path").is_err());
        assert!(validator.normalize(&temp_dir.path(), "../parent/path").is_err());
    }

    #[test]
    fn test_ensure_path_exists() {
        let temp_dir = tempdir().unwrap();
        let test_path = temp_dir.path().join("test_dir");

        // パスが存在しない場合は作成される
        assert!(!test_path.exists());
        ensure_path_exists(&test_path).unwrap();
        assert!(test_path.exists());
        assert!(test_path.is_dir());

        // パスが既に存在する場合はエラーにならない
        ensure_path_exists(&test_path).unwrap();
    }
} 