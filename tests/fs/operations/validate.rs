use std::fs::{self, File};
use tempfile::TempDir;
use anyhow::Result;

use cph::fs::operations::validate;

#[test]
fn test_exists() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_dir = temp_dir.path().join("test_dir");
    let non_existent = temp_dir.path().join("non_existent");

    // 存在しないパス
    assert!(validate::exists(&non_existent).is_err());

    // ファイルを作成して検証
    File::create(&test_file)?;
    assert!(validate::exists(&test_file).is_ok());

    // ディレクトリを作成して検証
    fs::create_dir(&test_dir)?;
    assert!(validate::exists(&test_dir).is_ok());

    Ok(())
}

#[test]
fn test_is_file() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_dir = temp_dir.path().join("test_dir");
    let non_existent = temp_dir.path().join("non_existent");

    // 存在しないパス
    assert!(validate::is_file(&non_existent).is_err());

    // ファイルを作成して検証
    File::create(&test_file)?;
    assert!(validate::is_file(&test_file).is_ok());

    // ディレクトリに対して検証
    fs::create_dir(&test_dir)?;
    assert!(validate::is_file(&test_dir).is_err());

    Ok(())
}

#[test]
fn test_is_dir() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_dir = temp_dir.path().join("test_dir");
    let non_existent = temp_dir.path().join("non_existent");

    // 存在しないパス
    assert!(validate::is_dir(&non_existent).is_err());

    // ディレクトリを作成して検証
    fs::create_dir(&test_dir)?;
    assert!(validate::is_dir(&test_dir).is_ok());

    // ファイルに対して検証
    File::create(&test_file)?;
    assert!(validate::is_dir(&test_file).is_err());

    Ok(())
}

#[test]
fn test_parent_exists() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let nested_file = temp_dir.path().join("nested/test.txt");
    let nested_dir = temp_dir.path().join("nested");

    // 親ディレクトリが存在する場合
    assert!(validate::parent_exists(&test_file).is_ok());

    // 親ディレクトリが存在しない場合
    assert!(validate::parent_exists(&nested_file).is_err());

    // 親ディレクトリを作成
    fs::create_dir(&nested_dir)?;
    assert!(validate::parent_exists(&nested_file).is_ok());

    Ok(())
} 