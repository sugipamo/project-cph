use std::sync::Arc;
use tempfile::TempDir;
use anyhow::Result;

use cph::fs::transaction::{Transaction, State, CreateFileOperation, DeleteFileOperation};

#[test]
fn test_transaction_new() {
    let transaction = Transaction::new();
    assert!(matches!(transaction.state(), State::Pending { .. }));
    assert!(transaction.operations().is_empty());
}

#[test]
fn test_create_file_operation() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_content = "Hello, World!";

    let operation = CreateFileOperation::new(test_file.clone(), test_content.to_string());
    let transaction = Transaction::new()
        .with_operation(Arc::new(operation))?
        .execute()?;

    assert!(matches!(transaction.state(), State::Executed { .. }));
    assert!(test_file.exists());
    assert_eq!(std::fs::read_to_string(&test_file)?, test_content);

    Ok(())
}

#[test]
fn test_delete_file_operation() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_content = "Hello, World!";

    // ファイルを作成
    std::fs::write(&test_file, test_content)?;
    assert!(test_file.exists());

    // ファイルを削除
    let operation = DeleteFileOperation::new(test_file.clone())?;
    let transaction = Transaction::new()
        .with_operation(Arc::new(operation))?
        .execute()?;

    assert!(matches!(transaction.state(), State::Executed { .. }));
    assert!(!test_file.exists());

    Ok(())
}

#[test]
fn test_transaction_rollback() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_content = "Hello, World!";

    // ファイルを作成するトランザクション
    let operation = CreateFileOperation::new(test_file.clone(), test_content.to_string());
    let transaction = Transaction::new()
        .with_operation(Arc::new(operation))?;

    // ロールバック
    let transaction = transaction.rollback()?;
    assert!(matches!(transaction.state(), State::RolledBack { .. }));
    assert!(!test_file.exists());

    Ok(())
}

#[test]
fn test_multiple_operations() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file1 = temp_dir.path().join("test1.txt");
    let test_file2 = temp_dir.path().join("test2.txt");
    let test_content = "Hello, World!";

    // 2つのファイルを作成するトランザクション
    let operation1 = CreateFileOperation::new(test_file1.clone(), test_content.to_string());
    let operation2 = CreateFileOperation::new(test_file2.clone(), test_content.to_string());

    let transaction = Transaction::new()
        .with_operation(Arc::new(operation1))?
        .with_operation(Arc::new(operation2))?
        .execute()?;

    assert!(matches!(transaction.state(), State::Executed { .. }));
    assert!(test_file1.exists());
    assert!(test_file2.exists());
    assert_eq!(std::fs::read_to_string(&test_file1)?, test_content);
    assert_eq!(std::fs::read_to_string(&test_file2)?, test_content);

    Ok(())
}

#[test]
fn test_transaction_error() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_content = "Hello, World!";

    // 先にファイルを作成
    std::fs::write(&test_file, test_content)?;

    // 既に存在するファイルを作成しようとする
    let operation = CreateFileOperation::new(test_file.clone(), test_content.to_string());
    let result = Transaction::new()
        .with_operation(Arc::new(operation));

    // 検証エラーが発生することを確認
    assert!(result.is_err());
    assert!(result.unwrap_err().to_string().contains("ファイルが既に存在します"));
    
    Ok(())
}

#[test]
fn test_transaction_description() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_content = "Hello, World!";

    let operation = CreateFileOperation::new(test_file.clone(), test_content.to_string());
    let transaction = Transaction::new()
        .with_operation(Arc::new(operation))?;

    let description = transaction.description();
    assert!(description.contains("トランザクション"));
    assert!(description.contains("保留中"));
    assert!(description.contains("test.txt"));

    Ok(())
} 