use tempfile::TempDir;
use anyhow::Result;

use cph::fs::Manager;

#[test]
fn test_manager_new() {
    let temp_dir = TempDir::new().unwrap();
    let manager = Manager::new(temp_dir.path());
    assert_eq!(manager.root_path(), temp_dir.path());
}

#[test]
fn test_file_operations() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let manager = Manager::new(temp_dir.path());

    // ファイルの存在確認（存在しない場合）
    assert!(!manager.exists("test.txt")?);

    // ファイルの書き込み
    let content = "Hello, World!";
    let manager = manager.write_file("test.txt", content)?;
    assert!(manager.exists("test.txt")?);

    // ファイルの読み込み
    assert_eq!(manager.read_file("test.txt")?, content);

    // ファイルの削除
    let manager = manager.delete_file("test.txt")?;
    assert!(!manager.exists("test.txt")?);

    Ok(())
}

#[test]
fn test_directory_operations() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let manager = Manager::new(temp_dir.path());

    // ディレクトリの存在確認（存在しない場合）
    assert!(!manager.exists("test_dir")?);

    // ディレクトリの作成
    let manager = manager.create_dir("test_dir")?;
    assert!(manager.exists("test_dir")?);

    // ネストしたディレクトリの作成
    let manager = manager.create_dir("test_dir/nested/deep")?;
    assert!(manager.exists("test_dir/nested/deep")?);

    Ok(())
}

#[test]
fn test_transaction_operations() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let manager = Manager::new(temp_dir.path());

    // トランザクション内でのファイル操作
    let manager = manager
        .begin_transaction()?
        .write_file("test1.txt", "Content 1")?
        .write_file("test2.txt", "Content 2")?
        .commit()?;

    assert!(manager.exists("test1.txt")?);
    assert!(manager.exists("test2.txt")?);
    assert_eq!(manager.read_file("test1.txt")?, "Content 1");
    assert_eq!(manager.read_file("test2.txt")?, "Content 2");

    // トランザクションのロールバック
    let manager = manager
        .begin_transaction()?
        .write_file("test3.txt", "Content 3")?
        .rollback()?;

    assert!(!manager.exists("test3.txt")?);

    Ok(())
}

#[test]
fn test_error_cases() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let manager = Manager::new(temp_dir.path());

    // 存在しないファイルの読み込み
    assert!(manager.clone().read_file("non_existent.txt").is_err());

    // 存在しないファイルの削除
    assert!(manager.clone().delete_file("non_existent.txt").is_err());

    // パストラバーサルの試行
    assert!(manager.clone().read_file("../test.txt").is_err());
    assert!(manager.clone().write_file("../test.txt", "content").is_err());

    // 絶対パスの試行
    assert!(manager.clone().read_file("/test.txt").is_err());
    assert!(manager.write_file("/test.txt", "content").is_err());

    Ok(())
}

#[test]
fn test_path_normalization() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let manager = Manager::new(temp_dir.path());

    // 通常のパス
    let manager = manager.write_file("test.txt", "content")?;
    assert!(manager.exists("test.txt")?);

    // カレントディレクトリを含むパス
    let manager = manager.write_file("./test2.txt", "content")?;
    assert!(manager.exists("test2.txt")?);

    // 重複したスラッシュを含むパス
    let manager = manager.write_file("dir//test3.txt", "content")?;
    assert!(manager.exists("dir/test3.txt")?);

    Ok(())
} 