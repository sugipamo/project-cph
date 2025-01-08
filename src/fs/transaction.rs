use std::path::PathBuf;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use anyhow::{Result, anyhow};
use crate::fs::ensure_path_exists;

/// ファイル操作のトレイト
pub trait FileOperation: Send + Sync + std::fmt::Debug {
    /// ファイル操作を実行します
    /// # Errors
    /// - ファイル操作に失敗した場合
    fn execute(&self) -> Result<()>;

    /// ファイル操作をロールバックします
    /// # Errors
    /// - ロールバックに失敗した場合
    fn rollback(&self) -> Result<()>;

    /// ファイル操作の説明を取得します
    #[must_use = "この関数の戻り値は操作の説明を含むため、使用する必要があります"]
    fn description(&self) -> String;

    /// ファイル操作の検証を行います
    /// # Errors
    /// - 検証に失敗した場合
    fn validate(&self) -> Result<()>;
}

/// トランザクションの状態を表す列挙型
#[derive(Debug, Clone)]
pub enum State {
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
        error: String,
        /// 失敗時のタイムスタンプ
        failed_at: u64,
    },
}

impl State {
    /// 現在のUNIXタイムスタンプを取得
    fn now() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_or(0, |duration| duration.as_secs())
    }

    /// 状態の説明を取得
    #[must_use = "状態の説明は重要な情報を含むため、使用する必要があります"]
    fn description(&self) -> String {
        match self {
            Self::Pending { created_at } => {
                format!("保留中 (作成: {created_at})")
            }
            Self::Executed { executed_at } => {
                format!("実行済み (実行: {executed_at})")
            }
            Self::RolledBack { rolled_back_at } => {
                format!("ロールバック済み (ロールバック: {rolled_back_at})")
            }
            Self::Failed { error, failed_at } => {
                format!("失敗 (時刻: {failed_at}): {error}")
            }
        }
    }
}

/// トランザクションの遷移を表す列挙型
#[derive(Debug, Clone)]
pub enum Transition {
    /// 操作の追加
    AddOperation(Arc<dyn FileOperation>),
    /// トランザクションの実行
    Execute,
    /// トランザクションのロールバック
    Rollback,
}

/// ファイルトランザクションを表す構造体
#[derive(Debug, Clone)]
pub struct Transaction {
    /// ファイル操作のリスト
    operations: Arc<Vec<Arc<dyn FileOperation>>>,
    /// トランザクションの状態
    state: State,
}

impl Default for Transaction {
    fn default() -> Self {
        Self::new()
    }
}

impl Transaction {
    /// 新しいトランザクションを作成します
    #[must_use = "新しいトランザクションインスタンスは使用する必要があります"]
    pub fn new() -> Self {
        Self {
            operations: Arc::new(Vec::new()),
            state: State::Pending {
                created_at: State::now(),
            },
        }
    }

    /// 操作を追加
    #[must_use]
    #[allow(dead_code)]
    fn with_operations(&self, operations: Vec<Arc<dyn FileOperation>>) -> Self {
        Self {
            operations: Arc::new(operations),
            state: self.state.clone(),
        }
    }

    /// 状態を更新
    #[must_use]
    fn with_state(&self, state: State) -> Self {
        Self {
            operations: Arc::clone(&self.operations),
            state,
        }
    }

    /// 状態遷移を適用します
    /// # Errors
    /// - 無効な状態遷移の場合
    /// - 操作の実行に失敗した場合
    /// - ロールバックに失敗した場合
    #[must_use = "状態遷移の結果は新しいトランザクションインスタンスとして返されます"]
    pub fn apply_transition(self, transition: Transition) -> Result<Self> {
        match (&self.state, transition) {
            (State::Pending { .. }, Transition::AddOperation(operation)) => {
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
            (State::Pending { .. }, Transition::Execute) => {
                // 全ての操作を実行
                for op in self.operations.iter() {
                    // 検証を実行
                    if let Err(e) = op.validate() {
                        return Ok(self.with_state(State::Failed {
                            error: e.to_string(),
                            failed_at: State::now(),
                        }));
                    }
                }

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
                        return Ok(self.with_state(State::Failed {
                            error: e.to_string(),
                            failed_at: State::now(),
                        }));
                    }
                }

                Ok(self.with_state(State::Executed {
                    executed_at: State::now(),
                }))
            }
            (State::Pending { .. }, Transition::Rollback) => {
                // 全ての操作をロールバック
                for op in self.operations.iter().rev() {
                    if let Err(e) = op.rollback() {
                        return Err(anyhow!("ロールバックに失敗: {}", e));
                    }
                }

                Ok(self.with_state(State::RolledBack {
                    rolled_back_at: State::now(),
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

    /// トランザクションの状態を取得します
    #[must_use = "トランザクションの状態は重要な情報を含むため、使用する必要があります"]
    pub const fn state(&self) -> &State {
        &self.state
    }

    /// トランザクションの説明を取得します
    #[must_use = "トランザクションの説明は重要な情報を含むため、使用する必要があります"]
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

    /// 操作を追加します
    /// # Errors
    /// - 操作の検証に失敗した場合
    #[must_use = "操作を追加した結果は新しいトランザクションインスタンスとして返されます"]
    pub fn with_operation(self, operation: Arc<dyn FileOperation>) -> Result<Self> {
        self.apply_transition(Transition::AddOperation(operation))
    }

    /// トランザクションを実行します
    /// # Errors
    /// - 操作の実行に失敗した場合
    /// - ロールバックに失敗した場合
    #[must_use = "トランザクションの実行結果は新しいトランザクションインスタンスとして返されます"]
    pub fn execute(self) -> Result<Self> {
        self.apply_transition(Transition::Execute)
    }

    /// トランザクションをロールバックします
    /// # Errors
    /// - ロールバックに失敗した場合
    #[must_use = "トランザクションのロールバック結果は新しいトランザクションインスタンスとして返されます"]
    pub fn rollback(self) -> Result<Self> {
        self.apply_transition(Transition::Rollback)
    }

    /// トランザクションの操作一覧を取得します
    #[must_use = "トランザクションの操作一覧は重要な情報を含むため、使用する必要があります"]
    pub fn operations(&self) -> &[Arc<dyn FileOperation>] {
        &self.operations
    }

    /// トランザクションを結合します
    /// # Errors
    /// - いずれかのトランザクションが保留状態でない場合
    #[must_use = "トランザクションの結合結果は新しいトランザクションインスタンスとして返されます"]
    pub fn combine(self, other: &Self) -> Result<Self> {
        match (&self.state, &other.state) {
            (State::Pending { .. }, State::Pending { .. }) => {
                let mut operations = (*self.operations).clone();
                operations.extend(other.operations.iter().cloned());
                Ok(Self {
                    operations: Arc::new(operations),
                    state: State::Pending {
                        created_at: State::now(),
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
    /// 新しいファイル作成操作を作成します
    #[must_use = "新しいファイル作成操作インスタンスは使用する必要があります"]
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
            .map_err(|e| anyhow!("ファイルの書き込みに失敗: {}: {}", self.path.display(), e))
    }

    fn rollback(&self) -> Result<()> {
        if self.path.exists() {
            std::fs::remove_file(&*self.path)
                .map_err(|e| anyhow!("ファイルの削除に失敗: {}: {}", self.path.display(), e))?;
        }
        Ok(())
    }

    fn description(&self) -> String {
        format!("ファイル作成: {}", self.path.display())
    }

    fn validate(&self) -> Result<()> {
        if self.path.as_os_str().is_empty() {
            return Err(anyhow!("パスが空です"));
        }
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
    /// 新しいファイル削除操作を作成します
    /// # Errors
    /// - ァイルの読み込みに失敗した場合
    #[must_use = "新しいファイル削除操作インスタンスは使用する必要があります"]
    pub fn new(path: PathBuf) -> Result<Self> {
        let original_content = if path.exists() {
            Some(Arc::new(std::fs::read_to_string(&path)
                .map_err(|e| anyhow!("ファイルの読み込みに失敗: {}: {}", path.display(), e))?))
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
                .map_err(|e| anyhow!("ファイルの削除に失敗: {}: {}", self.path.display(), e))?;
        }
        Ok(())
    }

    fn rollback(&self) -> Result<()> {
        if let Some(content) = &self.original_content {
            if let Some(parent) = self.path.parent() {
                ensure_path_exists(parent)?;
            }
            std::fs::write(&*self.path, &**content)
                .map_err(|e| anyhow!("ファイルの復元に失敗: {}: {}", self.path.display(), e))?;
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
