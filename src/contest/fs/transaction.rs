use std::path::{Path, PathBuf};
use crate::contest::error::{Result, ContestError, ErrorContext};
use super::backup::BackupManager;
use std::collections::VecDeque;

/// ファイルシステム操作のトランザクション
#[derive(Debug)]
pub struct FileTransaction {
    /// 実行予定の操作キュー
    operations: VecDeque<Box<dyn FileOperation>>,
    /// バックアップマネージャー
    backup: BackupManager,
    /// トランザクションの状態
    state: TransactionState,
    /// エラーコンテキスト
    context: ErrorContext,
}

/// トランザクションの状態
#[derive(Debug, Clone, Copy, PartialEq)]
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
pub trait FileOperation: std::fmt::Debug {
    /// 操作を実行
    fn execute(&self) -> Result<()>;
    /// 操作を取り消し
    fn rollback(&self) -> Result<()>;
    /// 操作の説明を取得
    fn description(&self) -> String;
}

impl FileTransaction {
    /// 新しいトランザクションを作成
    pub fn new(operation_name: impl Into<String>) -> Result<Self> {
        Ok(Self {
            operations: VecDeque::new(),
            backup: BackupManager::new()?,
            state: TransactionState::Initial,
            context: ErrorContext::new(operation_name, "FileTransaction"),
        })
    }

    /// 操作を追加
    pub fn add_operation(&mut self, operation: impl FileOperation + 'static) -> &mut Self {
        self.operations.push_back(Box::new(operation));
        self
    }

    /// トランザクションを実行
    pub fn execute(&mut self) -> Result<()> {
        if self.state != TransactionState::Initial {
            return Err(ContestError::Transaction {
                message: "トランザクションは既に実行されています".to_string(),
                context: self.context.clone()
                    .with_hint("トランザクションは一度だけ実行できます")
                    .with_stack_trace(),
            });
        }

        self.state = TransactionState::InProgress;
        
        // バックアップを作成
        if let Err(e) = self.backup.create(&PathBuf::from(".")) {
            return Err(e.with_context("バックアップの作成", ".")
                .add_hint("バックアップディレクトリの権限を確認してください"));
        }

        // 全ての操作を実行
        while let Some(operation) = self.operations.pop_front() {
            if let Err(e) = operation.execute() {
                // エラーが発生した場合はロールバック
                if let Err(rollback_err) = self.rollback() {
                    return Err(ContestError::Transaction {
                        message: format!(
                            "操作の実行とロールバックの両方が失敗しました: {} / {}",
                            e, rollback_err
                        ),
                        context: self.context.clone()
                            .with_hint("システム管理者に連絡してください")
                            .with_stack_trace(),
                    });
                }
                return Err(e.with_context(
                    "トランザクション操作の実行",
                    operation.description()
                ).add_hint("操作をロールバックしました"));
            }
        }

        self.state = TransactionState::Committed;
        if let Err(e) = self.backup.cleanup() {
            return Err(e.with_context("バックアップのクリーンアップ", ".")
                .add_hint("バックアップファイルの削除に失敗しましたが、操作自体は成功しています"));
        }
        Ok(())
    }

    /// トランザクションをロールバック
    pub fn rollback(&mut self) -> Result<()> {
        if self.state != TransactionState::InProgress {
            return Ok(());
        }

        // バックアップから復元
        if let Err(e) = self.backup.restore() {
            return Err(e.with_context("バックアップの復元", ".")
                .add_hint("システムの状態が不整合である可能性があります"));
        }
        self.state = TransactionState::RolledBack;
        if let Err(e) = self.backup.cleanup() {
            return Err(e.with_context("バックアップのクリーンアップ", ".")
                .add_hint("バックアップファイルの削除に失敗しましたが、ロールバックは成功しています"));
        }
        Ok(())
    }

    /// 現在の状態を取得
    pub fn state(&self) -> TransactionState {
        self.state
    }
} 