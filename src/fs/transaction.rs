use std::fmt::Debug;
use crate::error::Result;
use super::error::fs_err;

/// ファイル操作のトランザクション状態
#[derive(Debug, PartialEq)]
pub enum TransactionState {
    /// 初期状態
    Initial,
    /// 実行中
    InProgress,
    /// コミット済み
    Committed,
    /// ロールバック済み
    RolledBack,
}

/// ファイル操作のトレイト
pub trait FileOperation: Debug {
    /// 操作を実行
    fn execute(&self) -> Result<()>;
    /// 操作をロールバック
    fn rollback(&self) -> Result<()>;
}

/// ファイル操作のトランザクション
#[derive(Debug)]
pub struct FileTransaction {
    /// 操作のリスト
    operations: Vec<Box<dyn FileOperation>>,
    /// トランザクションの状態
    state: TransactionState,
}

impl FileTransaction {
    /// 新しいトランザクションを作成
    pub fn new(operations: Vec<Box<dyn FileOperation>>) -> Self {
        Self {
            operations,
            state: TransactionState::Initial,
        }
    }

    /// トランザクションを実行
    pub fn execute(&mut self) -> Result<()> {
        if self.state != TransactionState::Initial {
            return Err(fs_err("トランザクションは既に実行されています".to_string()));
        }

        self.state = TransactionState::InProgress;

        // 各操作を実行
        for operation in &self.operations {
            if let Err(e) = operation.execute() {
                // エラーが発生した場合、ロールバック
                self.rollback()?;
                return Err(fs_err(format!("操作の実行中にエラーが発生しました: {}", e)));
            }
        }

        self.state = TransactionState::Committed;
        Ok(())
    }

    /// トランザクションをロールバック
    pub fn rollback(&mut self) -> Result<()> {
        if self.state != TransactionState::InProgress {
            return Ok(());
        }

        // 逆順で各操作をロールバック
        for operation in self.operations.iter().rev() {
            if let Err(e) = operation.rollback() {
                return Err(fs_err(format!("ロールバック中にエラーが発生しました: {}", e)));
            }
        }

        self.state = TransactionState::RolledBack;
        Ok(())
    }

    /// トランザクションの状態を取得
    pub fn state(&self) -> &TransactionState {
        &self.state
    }
} 