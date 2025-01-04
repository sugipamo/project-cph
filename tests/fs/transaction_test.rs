use std::path::PathBuf;
use tempfile::TempDir;
use crate::contest::fs::{
    FileTransaction,
    CopyOperation,
    CreateDirOperation,
    RemoveOperation,
    TransactionState,
};

#[tokio::test]
async fn test_transaction_basic_operations() -> anyhow::Result<()> {
    // テスト用の一時ディレクトリを作成
    let temp_dir = TempDir::new()?;
    let base_path = temp_dir.path();

    // テストファイルとディレクトリのパスを設定
    let test_dir = base_path.join("test_dir");
    let test_file = base_path.join("test.txt");
    let copied_file = base_path.join("test_copy.txt");

    // テストファイルを作成
    std::fs::write(&test_file, "test content")?;

    // トランザクションを作成
    let mut transaction = FileTransaction::new("test_basic_operations")?;

    // 操作を追加
    transaction
        .add_operation(CreateDirOperation::new(&test_dir))
        .add_operation(CopyOperation::new(&test_file, &copied_file));

    // トランザクションを実行
    transaction.execute()?;

    // 結果を検証
    assert!(test_dir.exists());
    assert!(copied_file.exists());
    assert_eq!(std::fs::read_to_string(&copied_file)?, "test content");

    Ok(())
}

#[tokio::test]
async fn test_transaction_rollback() -> anyhow::Result<()> {
    let temp_dir = TempDir::new()?;
    let base_path = temp_dir.path();

    // テストファイルを作成
    let test_file = base_path.join("test.txt");
    std::fs::write(&test_file, "test content")?;

    // 意図的に失敗する操作を含むトランザクションを作成
    let mut transaction = FileTransaction::new("test_rollback")?;

    // 正常な操作を追加
    transaction.add_operation(CopyOperation::new(
        &test_file,
        base_path.join("copy1.txt"),
    ));

    // 存在しないファイルを削除する操作（失敗する）
    transaction.add_operation(RemoveOperation::new(
        base_path.join("non_existent.txt"),
        false,
    ));

    // トランザクションを実行（失敗するはず）
    let result = transaction.execute();
    assert!(result.is_err());

    // ロールバックが行われたことを確認
    assert_eq!(transaction.state(), TransactionState::RolledBack);
    assert!(!base_path.join("copy1.txt").exists());

    Ok(())
}

#[tokio::test]
async fn test_transaction_state_transitions() -> anyhow::Result<()> {
    let temp_dir = TempDir::new()?;
    let base_path = temp_dir.path();

    let mut transaction = FileTransaction::new("test_states")?;
    assert_eq!(transaction.state(), TransactionState::Initial);

    // 操作を追加
    transaction.add_operation(CreateDirOperation::new(
        base_path.join("test_dir"),
    ));

    // 実行
    transaction.execute()?;
    assert_eq!(transaction.state(), TransactionState::Committed);

    // 同じトランザクションの再実行を試みる
    let result = transaction.execute();
    assert!(result.is_err());

    Ok(())
}

#[tokio::test]
async fn test_complex_transaction() -> anyhow::Result<()> {
    let temp_dir = TempDir::new()?;
    let base_path = temp_dir.path();

    // 複数の階層のディレクトリとファイルを作成
    let dir1 = base_path.join("dir1");
    let dir2 = dir1.join("dir2");
    let file1 = dir1.join("file1.txt");
    let file2 = dir2.join("file2.txt");

    let mut transaction = FileTransaction::new("test_complex")?;

    // 複数の操作を追加
    transaction
        .add_operation(CreateDirOperation::new(&dir1))
        .add_operation(CreateDirOperation::new(&dir2));

    // ファイルを作成
    std::fs::write(base_path.join("source1.txt"), "content1")?;
    std::fs::write(base_path.join("source2.txt"), "content2")?;

    // ファイルをコピー
    transaction
        .add_operation(CopyOperation::new(
            base_path.join("source1.txt"),
            &file1,
        ))
        .add_operation(CopyOperation::new(
            base_path.join("source2.txt"),
            &file2,
        ));

    // トランザクションを実行
    transaction.execute()?;

    // 結果を検証
    assert!(dir1.exists());
    assert!(dir2.exists());
    assert!(file1.exists());
    assert!(file2.exists());
    assert_eq!(std::fs::read_to_string(&file1)?, "content1");
    assert_eq!(std::fs::read_to_string(&file2)?, "content2");

    Ok(())
} 