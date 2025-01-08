use std::fs::{self, File};
use std::io::Write;
use tempfile::TempDir;
use anyhow::Result;

use cph::fs::operations::read;

#[test]
fn test_load_file_as_string() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_content = "Hello, World!";

    // ファイルが存在しない場合
    assert!(read::load_file_as_string(&test_file).is_err());

    // 通常のテキストファイル
    {
        let mut file = File::create(&test_file)?;
        write!(file, "{}", test_content)?;
    }
    let content = read::load_file_as_string(&test_file)?;
    assert_eq!(content, test_content);

    // ディレクトリを読み込もうとした場合
    let test_dir = temp_dir.path().join("test_dir");
    fs::create_dir(&test_dir)?;
    assert!(read::load_file_as_string(&test_dir).is_err());

    // 非UTF-8文字列を含むファイル
    {
        let mut file = File::create(&test_file)?;
        file.write_all(&[0xFF, 0xFF, 0xFF])?;
    }
    assert!(read::load_file_as_string(&test_file).is_err());

    Ok(())
}

#[test]
fn test_load_file_as_bytes() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.bin");
    let test_bytes = vec![1, 2, 3, 4, 5];

    // ファイルが存在しない場合
    assert!(read::load_file_as_bytes(&test_file).is_err());

    // バイナリファイル
    {
        let mut file = File::create(&test_file)?;
        file.write_all(&test_bytes)?;
    }
    let content = read::load_file_as_bytes(&test_file)?;
    assert_eq!(content, test_bytes);

    // ディレクトリを読み込もうとした場合
    let test_dir = temp_dir.path().join("test_dir");
    fs::create_dir(&test_dir)?;
    assert!(read::load_file_as_bytes(&test_dir).is_err());

    // 大きなファイル
    {
        let mut file = File::create(&test_file)?;
        let large_bytes = vec![0; 1024 * 1024]; // 1MB
        file.write_all(&large_bytes)?;
    }
    let content = read::load_file_as_bytes(&test_file)?;
    assert_eq!(content.len(), 1024 * 1024);

    Ok(())
}

#[test]
fn test_get_metadata() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_content = "Hello, World!";

    // ファイルが存在しない場合
    assert!(read::get_metadata(&test_file).is_err());

    // ファイルのメタデータを取得
    {
        let mut file = File::create(&test_file)?;
        write!(file, "{}", test_content)?;
    }
    let metadata = read::get_metadata(&test_file)?;
    assert!(metadata.is_file());
    assert_eq!(metadata.len(), test_content.len() as u64);

    // ディレクトリのメタデータを取得しようとした場合
    let test_dir = temp_dir.path().join("test_dir");
    fs::create_dir(&test_dir)?;
    assert!(read::get_metadata(&test_dir).is_err());

    Ok(())
} 