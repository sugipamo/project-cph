use std::path::PathBuf;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use anyhow::{Result, anyhow, Context, Error};
use crate::fs::ensure_path_exists;

/// ファイル操作のトレイト
pub trait FileOperation: Send + Sync + std::fmt::Debug {
    fn execute(&self) -> Result<()>;
    fn rollback(&self) -> Result<()>;
    fn description(&self) -> String;
    fn validate(&self) -> Result<()>;
}

/// トランザクションの状態を表す列挙型
#[derive(Debug, Clone)]
pub enum TransactionState {
    /// 初期状態
    Pending {
        /// 作成時のタイムスタンプ
        created_at: u64,
    },
    /// 実行済み
    Executed {
        /// 実行時のタイムスタンプ
        executed_at: u64,
    },
    /// ロールバック済み
    RolledBack {
        /// ロールバック時のタイムスタンプ
        rolled_back_at: u64,
    },
    /// 失敗
    Failed {
        /// エラー情報
        error: Arc<Error>,
        /// 失敗時のタイムスタンプ
        failed_at: u64,
    },
}

impl TransactionState {
    /// 現在のUNIXタイムスタンプを取得
    fn now() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs()
    }

    /// 状態の説明を取得
    fn description(&self) -> String {
        match self {
            Self::Pending { created_at } => {
                format!("保留中 (作成: {})", created_at)
            }
            Self::Executed { executed_at } => {
                format!("実行済み (実行: {})", executed_at)
            }
            Self::RolledBack { rolled_back_at } => {
                format!("ロールバック済み (ロールバック: {})", rolled_back_at)
            }
            Self::Failed { error, failed_at } => {
                format!("失敗 (時刻: {}): {}", failed_at, error)
            }
        }
    }
}

/// トランザクションの遷移を表す列挙型
#[derive(Debug, Clone)]
pub enum TransactionTransition {
    /// 操作の追加
    AddOperation(Arc<dyn FileOperation>),
    /// トランザクションの実行
    Execute,
    /// トランザクションのロールバック
    Rollback,
}

/// ファイルトランザクションを表す構造体
#[derive(Debug, Clone)]
pub struct FileTransaction {
    /// ファイル操作のリスト
    operations: Arc<Vec<Arc<dyn FileOperation>>>,
    /// トランザクションの状態
    state: TransactionState,
}

impl FileTransaction {
    /// 新しいトランザクションを作成
    pub fn new() -> Self {
        Self {
            operations: Arc::new(Vec::new()),
            state: TransactionState::Pending {
                created_at: TransactionState::now(),
            },
        }
    }

    /// 操作を追加
    fn with_operations(&self, operations: Vec<Arc<dyn FileOperation>>) -> Self {
        Self {
            operations: Arc::new(operations),
            state: self.state.clone(),
        }
    }

    /// 状態を更新
    fn with_state(&self, state: TransactionState) -> Self {
        Self {
            operations: Arc::clone(&self.operations),
            state,
        }
    }

    /// 状態遷移を適用
    pub fn apply_transition(self, transition: TransactionTransition) -> Result<Self> {
        match (&self.state, transition) {
            (TransactionState::Pending { .. }, TransactionTransition::AddOperation(operation)) => {
                // 操作の検証
                if let Err(e) = operation.validate() {
                    return Err(anyhow!("操作の検証に失敗: {}", e));
                }

                let mut operations = (*self.operations).clone();
                operations.push(operation);

                Ok(Self {
                    operations: Arc::new(operations),
                    state: self.state,
                })
            }
            (TransactionState::Pending { .. }, TransactionTransition::Execute) => {
                // 全ての操作を実行
                for op in self.operations.iter() {
                    if let Err(e) = op.execute() {
                        // エラーが発生した場合、実行済みの操作をロールバック
                        for prev_op in self.operations.iter().rev() {
                            if let Err(rollback_err) = prev_op.rollback() {
                                return Err(anyhow!(
                                    "ロールバックに失敗: {}（元のエラー: {}）",
                                    rollback_err, e
                                ));
                            }
                        }
                        return Ok(self.with_state(TransactionState::Failed {
                            error: Arc::new(e),
                            failed_at: TransactionState::now(),
                        }));
                    }
                }

                Ok(self.with_state(TransactionState::Executed {
                    executed_at: TransactionState::now(),
                }))
            }
            (TransactionState::Pending { .. }, TransactionTransition::Rollback) => {
                // 全ての操作をロールバック
                for op in self.operations.iter().rev() {
                    if let Err(e) = op.rollback() {
                        return Err(anyhow!("ロールバックに失敗: {}", e));
                    }
                }

                Ok(self.with_state(TransactionState::RolledBack {
                    rolled_back_at: TransactionState::now(),
                }))
            }
            (state, transition) => {
                Err(anyhow!(
                    "無効な状態遷移です: {:?} -> {:?}",
                    state, transition
                ))
            }
        }
    }

    /// トランザクションの状態を取得
    pub fn state(&self) -> &TransactionState {
        &self.state
    }

    /// トランザクションの説明を取得
    pub fn description(&self) -> String {
        format!(
            "トランザクション（{}）:\n{}",
            self.state.description(),
            self.operations
                .iter()
                .enumerate()
                .map(|(i, op)| format!("  {}: {}", i + 1, op.description()))
                .collect::<Vec<_>>()
                .join("\n")
        )
    }

    /// 操作を追加
    pub fn with_operation(self, operation: Arc<dyn FileOperation>) -> Result<Self> {
        self.apply_transition(TransactionTransition::AddOperation(operation))
    }

    /// トランザクションを実行
    pub fn execute(self) -> Result<Self> {
        self.apply_transition(TransactionTransition::Execute)
    }

    /// トランザクションをロールバック
    pub fn rollback(self) -> Result<Self> {
        self.apply_transition(TransactionTransition::Rollback)
    }

    /// トランザクションの操作一覧を取得
    pub fn operations(&self) -> &[Arc<dyn FileOperation>] {
        &self.operations
    }

    /// トランザクションを結合
    pub fn combine(self, other: Self) -> Result<Self> {
        match (&self.state, &other.state) {
            (TransactionState::Pending { .. }, TransactionState::Pending { .. }) => {
                let mut operations = (*self.operations).clone();
                operations.extend(other.operations.iter().cloned());
                Ok(Self {
                    operations: Arc::new(operations),
                    state: TransactionState::Pending {
                        created_at: TransactionState::now(),
                    },
                })
            }
            _ => {
                Err(anyhow!("トランザクションの結合は保留状態でのみ可能です"))
            }
        }
    }
}

// イミュータブルな操作を実装するための具体的な型
#[derive(Debug)]
pub struct CreateFileOperation {
    path: Arc<PathBuf>,
    content: Arc<String>,
}

impl CreateFileOperation {
    pub fn new(path: PathBuf, content: String) -> Self {
        Self {
            path: Arc::new(path),
            content: Arc::new(content),
        }
    }
}

impl FileOperation for CreateFileOperation {
    fn execute(&self) -> Result<()> {
        if let Some(parent) = self.path.parent() {
            ensure_path_exists(parent)?;
        }
        std::fs::write(&*self.path, &*self.content)
            .context(format!("ファイルの書き込みに失敗: {}", self.path.display()))
    }

    fn rollback(&self) -> Result<()> {
        if self.path.exists() {
            std::fs::remove_file(&*self.path)
                .context(format!("ファイルの削除に失敗: {}", self.path.display()))?;
        }
        Ok(())
    }

    fn description(&self) -> String {
        format!("ファイル作成: {}", self.path.display())
    }

    fn validate(&self) -> Result<()> {
        if self.path.exists() {
            return Err(anyhow!("ファイルが既に存在します: {}", self.path.display()));
        }
        Ok(())
    }
}

#[derive(Debug)]
pub struct DeleteFileOperation {
    path: Arc<PathBuf>,
    original_content: Option<Arc<String>>,
}

impl DeleteFileOperation {
    pub fn new(path: PathBuf) -> Result<Self> {
        let original_content = if path.exists() {
            Some(Arc::new(std::fs::read_to_string(&path)
                .context(format!("ファイルの読み込みに失敗: {}", path.display()))?))
        } else {
            None
        };

        Ok(Self {
            path: Arc::new(path),
            original_content,
        })
    }
}

impl FileOperation for DeleteFileOperation {
    fn execute(&self) -> Result<()> {
        if self.path.exists() {
            std::fs::remove_file(&*self.path)
                .context(format!("ファイルの削除に失敗: {}", self.path.display()))?;
        }
        Ok(())
    }

    fn rollback(&self) -> Result<()> {
        if let Some(content) = &self.original_content {
            if let Some(parent) = self.path.parent() {
                ensure_path_exists(parent)?;
            }
            std::fs::write(&*self.path, &**content)
                .context(format!("ファイルの復元に失敗: {}", self.path.display()))?;
        }
        Ok(())
    }

    fn description(&self) -> String {
        format!("ファイル削除: {}", self.path.display())
    }

    fn validate(&self) -> Result<()> {
        if !self.path.exists() {
            return Err(anyhow!("ファイルが存在しません: {}", self.path.display()));
        }
        Ok(())
    }
}

#[derive(Debug)]
pub struct TransactionError {
    operation: Arc<dyn FileOperation>,
    error: Arc<Error>,
} 
