use std::fs::{self, File};
use tempfile::TempDir;
use anyhow::Result;

use cph::fs::operations::{delete, check_exists};

#[test]
fn test_remove_file() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");

    // ファイルが存在しない場合
    assert!(delete::remove_file(&test_file).is_err());

    // ファイルを作成して削除
    File::create(&test_file)?;
    assert!(check_exists(&test_file));
    assert!(delete::remove_file(&test_file).is_ok());
    assert!(!check_exists(&test_file));

    // ディレクトリを削除しようとした場合
    let test_dir = temp_dir.path().join("test_dir");
    fs::create_dir(&test_dir)?;
    assert!(delete::remove_file(&test_dir).is_err());

    Ok(())
}

#[test]
fn test_remove_dir() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_dir = temp_dir.path().join("test_dir");
    let nested_dir = test_dir.join("nested");
    let nested_file = nested_dir.join("test.txt");

    // ディレクトリが存在しない場合
    assert!(delete::remove_dir(&test_dir).is_err());

    // 空のディレクトリを作成して削除
    fs::create_dir(&test_dir)?;
    assert!(check_exists(&test_dir));
    assert!(delete::remove_dir(&test_dir).is_ok());
    assert!(!check_exists(&test_dir));

    // ネストしたディレクトリとファイルを含むディレクトリを削除
    fs::create_dir_all(&nested_dir)?;
    File::create(&nested_file)?;
    assert!(check_exists(&nested_file));
    assert!(delete::remove_dir(&test_dir).is_ok());
    assert!(!check_exists(&test_dir));
    assert!(!check_exists(&nested_dir));
    assert!(!check_exists(&nested_file));

    // ファイルを削除しようとした場合
    let test_file = temp_dir.path().join("test.txt");
    File::create(&test_file)?;
    assert!(delete::remove_dir(&test_file).is_err());

    Ok(())
} 