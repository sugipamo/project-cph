use std::fs::File;
use std::io::{Write, Read};
use tempfile::TempDir;
use anyhow::Result;
use tokio;

use cph::fs::backup::Manager;

#[tokio::test]
async fn test_backup_manager_new() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let backup_dir = temp_dir.path().join("backup");

    // バックアップディレクトリが存在しない場合
    assert!(!backup_dir.exists());
    let _manager = Manager::new(&backup_dir).await?;
    assert!(backup_dir.exists());

    // バックアップディレクトリが既に存在する場合
    let _manager = Manager::new(&backup_dir).await?;
    assert!(backup_dir.exists());

    Ok(())
}

#[tokio::test]
async fn test_backup_and_restore() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let backup_dir = temp_dir.path().join("backup");
    let test_file = temp_dir.path().join("test.txt");
    let test_content = "Hello, World!";

    // バックアップマネージャを作成
    let manager = Manager::new(&backup_dir).await?;

    // テストファイルを作成
    {
        let mut file = File::create(&test_file)?;
        write!(file, "{}", test_content)?;
    }

    // バックアップを作成
    manager.backup(&test_file).await?;

    // バックアップファイルの一覧を取得
    let backups = manager.list_backups("test.txt").await?;
    assert_eq!(backups.len(), 1);

    // 元のファイルを変更
    {
        let mut file = File::create(&test_file)?;
        write!(file, "Modified content")?;
    }

    // バックアップから復元
    manager.restore(&test_file, &backups[0]).await?;

    // 復元されたファイルの内容を確認
    let mut content = String::new();
    File::open(&test_file)?.read_to_string(&mut content)?;
    assert_eq!(content, test_content);

    Ok(())
}

#[tokio::test]
async fn test_multiple_backups() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let backup_dir = temp_dir.path().join("backup");
    let test_file = temp_dir.path().join("test.txt");

    // バックアップマネージャを作成
    let manager = Manager::new(&backup_dir).await?;

    // 複数のバックアップを作成
    for i in 1..=3 {
        {
            let mut file = File::create(&test_file)?;
            write!(file, "Content {}", i)?;
        }
        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
        manager.backup(&test_file).await?;
    }

    // バックアップファイルの一覧を取得
    let mut backups = manager.list_backups("test.txt").await?;
    assert_eq!(backups.len(), 3);

    // バックアップファイルを時系列順にソート
    backups.sort();

    // 最新のバックアップから復元
    manager.restore(&test_file, &backups[2]).await?;

    // 復元されたファイルの内容を確認
    let mut content = String::new();
    File::open(&test_file)?.read_to_string(&mut content)?;
    assert_eq!(content, "Content 3");

    Ok(())
}

#[tokio::test]
async fn test_backup_error_cases() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let backup_dir = temp_dir.path().join("backup");
    let test_file = temp_dir.path().join("test.txt");
    let non_existent_file = temp_dir.path().join("non_existent.txt");

    // バックアップマネージャを作成
    let manager = Manager::new(&backup_dir).await?;

    // 存在しないファイルのバックアップ
    assert!(manager.backup(&non_existent_file).await.is_ok());

    // 存在しないバックアップファイルからの復元
    assert!(manager.restore(&test_file, "non_existent.bak").await.is_err());

    // 存在しないファイルのバックアップ一覧
    let backups = manager.list_backups("non_existent.txt").await?;
    assert!(backups.is_empty());

    Ok(())
} 