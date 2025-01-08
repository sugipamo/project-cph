use std::fs::File;
use std::io::Read;
use tempfile::TempDir;
use anyhow::Result;

use cph::fs::operations::{write, check_exists, check_is_file, check_is_directory};

#[test]
fn test_ensure_directory() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_dir = temp_dir.path().join("test_dir");
    let nested_dir = test_dir.join("nested/deep/path");

    // ディレクトリが存在しない場合
    assert!(!check_exists(&test_dir));
    write::ensure_directory(&test_dir)?;
    assert!(check_exists(&test_dir));
    assert!(check_is_directory(&test_dir));

    // ネストしたディレクトリの作成
    assert!(!check_exists(&nested_dir));
    write::ensure_directory(&nested_dir)?;
    assert!(check_exists(&nested_dir));
    assert!(check_is_directory(&nested_dir));

    // 既に存在するディレクトリ
    write::ensure_directory(&test_dir)?;
    assert!(check_exists(&test_dir));
    assert!(check_is_directory(&test_dir));

    Ok(())
}

#[test]
fn test_ensure_file() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let nested_dir = temp_dir.path().join("nested/dir");
    let nested_file = nested_dir.join("test.txt");

    // ファイルが存在しない場合
    assert!(!check_exists(&test_file));
    write::ensure_file(&test_file)?;
    assert!(check_exists(&test_file));
    assert!(check_is_file(&test_file));

    // 親ディレクトリを作成してからファイルを作成
    write::ensure_directory(&nested_dir)?;
    assert!(!check_exists(&nested_file));
    write::ensure_file(&nested_file)?;
    assert!(check_exists(&nested_file));
    assert!(check_is_file(&nested_file));

    // 既に存在するファイル
    write::ensure_file(&test_file)?;
    assert!(check_exists(&test_file));
    assert!(check_is_file(&test_file));

    Ok(())
}

#[test]
fn test_save_to_file() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let nested_file = temp_dir.path().join("nested/dir/test.txt");
    let test_content = "Hello, World!";
    let binary_content = vec![1, 2, 3, 4, 5];

    // テキストファイルの書き込み
    write::save_to_file(&test_file, test_content)?;
    assert!(check_exists(&test_file));
    let mut content = String::new();
    File::open(&test_file)?.read_to_string(&mut content)?;
    assert_eq!(content, test_content);

    // 親ディレクトリが存在しないファイルへの書き込み
    write::save_to_file(&nested_file, test_content)?;
    assert!(check_exists(&nested_file));
    let mut content = String::new();
    File::open(&nested_file)?.read_to_string(&mut content)?;
    assert_eq!(content, test_content);

    // バイナリデータの書き込み
    write::save_to_file(&test_file, &binary_content)?;
    let mut content = Vec::new();
    File::open(&test_file)?.read_to_end(&mut content)?;
    assert_eq!(content, binary_content);

    // 既存ファイルの上書き
    let new_content = "New content";
    write::save_to_file(&test_file, new_content)?;
    let mut content = String::new();
    File::open(&test_file)?.read_to_string(&mut content)?;
    assert_eq!(content, new_content);

    Ok(())
} 