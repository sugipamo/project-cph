use tempfile::TempDir;
use anyhow::Result;

use cph::fs::path::{self, ValidationLevel, Validator};

#[test]
fn test_validator_default() {
    let validator = Validator::default();
    assert!(validator.validate("test.txt").is_ok());
    assert!(validator.validate("a".repeat(256)).is_err());
}

#[test]
fn test_validator_new() {
    let validator = Validator::new(ValidationLevel::Strict, 1024, 128);
    assert!(validator.validate("test.txt").is_ok());
    assert!(validator.validate("a".repeat(129)).is_err());
}

#[test]
fn test_validate() -> Result<()> {
    let validator = Validator::default();

    // 有効なパス
    assert!(validator.validate("test.txt").is_ok());
    assert!(validator.validate("dir/test.txt").is_ok());
    assert!(validator.validate("dir/subdir/test.txt").is_ok());

    // 無効なパス（パストラバーサル）
    assert!(validator.validate("../test.txt").is_err());
    assert!(validator.validate("dir/../test.txt").is_err());
    assert!(validator.validate("dir/../../test.txt").is_err());

    // 無効なパス（絶対パス）
    assert!(validator.validate("/test.txt").is_err());
    assert!(validator.validate("/dir/test.txt").is_err());

    // 無効なパス（ファイル名が長すぎる）
    let long_filename = "a".repeat(256);
    assert!(validator.validate(long_filename).is_err());

    Ok(())
}

#[test]
fn test_normalize() -> Result<()> {
    let validator = Validator::default();
    let temp_dir = TempDir::new()?;
    let root = temp_dir.path();

    // 通常のパス
    let path = "test.txt";
    let normalized = validator.normalize(root, path)?;
    assert_eq!(normalized, root.join(path));

    // ディレクトリを含むパス
    let path = "dir/test.txt";
    let normalized = validator.normalize(root, path)?;
    assert_eq!(normalized, root.join(path));

    // カレントディレクトリを含むパス
    let path = "./test.txt";
    let normalized = validator.normalize(root, path)?;
    assert_eq!(normalized, root.join("test.txt"));

    // 無効なパス
    let path = "../test.txt";
    assert!(validator.normalize(root, path).is_err());

    Ok(())
}

#[test]
fn test_path_functions() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let root = temp_dir.path();

    // normalize関数のテスト
    let path = "test.txt";
    let normalized = path::normalize(root, path)?;
    assert_eq!(normalized, root.join(path));

    // validate関数のテスト
    assert!(path::validate("test.txt").is_ok());
    assert!(path::validate("../test.txt").is_err());

    // ensure_path_exists関数のテスト
    let test_dir = temp_dir.path().join("test_dir");
    assert!(!test_dir.exists());
    path::ensure_path_exists(&test_dir)?;
    assert!(test_dir.exists());

    Ok(())
} 