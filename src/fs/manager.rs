use std::path::{Path, PathBuf};
use std::sync::Arc;
use anyhow::{Result, anyhow};
use crate::fs::path::normalize;
use crate::fs::{FileOperation, Transaction, CreateFileOperation, DeleteFileOperation};

/// ファイル管理の状態を表現する型
#[derive(Debug, Clone)]
pub enum State {
    /// アイドル状態
    Idle,
    /// トランザクション実行中
    InTransaction(Transaction),
}

/// 状態遷移を表現する型
#[derive(Debug, Clone)]
pub enum Transition {
    /// トランザクションの開始
    BeginTransaction,
    /// 操作の追加
    AddOperation(Arc<dyn FileOperation>),
    /// トランザクションのコミット
    Commit,
    /// トランザクションのロールバック
    Rollback,
}

/// ファイル管理を行う構造体
#[derive(Debug, Clone)]
pub struct Manager {
    root: Arc<PathBuf>,
    state: State,
}

impl Manager {
    /// 新しいファイルシステムインスタンスを作成します。
    /// 
    /// # Arguments
    /// * `root` - ルートディレクトリのパス
    #[must_use = "この関数は新しいManagerインスタンスを返します"]
    pub fn new(root: impl Into<PathBuf>) -> Self {
        Self {
            root: Arc::new(root.into()),
            state: State::Idle,
        }
    }

    /// 状態遷移を適用します。
    /// 
    /// # Arguments
    /// * `transition` - 適用する状態遷移
    /// 
    /// # Errors
    /// - 無効な状態遷移が指定された場合
    #[must_use = "この関数は新しいManagerインスタンスを返します"]
    fn apply_transition(self, transition: Transition) -> Result<Self> {
        match (self.state, transition) {
            (State::Idle, Transition::BeginTransaction) => {
                Ok(Self {
                    root: self.root,
                    state: State::InTransaction(Transaction::new()),
                })
            },
            (State::InTransaction(transaction), Transition::AddOperation(operation)) => {
                let new_transaction = transaction.with_operation(operation)?;
                Ok(Self {
                    root: self.root,
                    state: State::InTransaction(new_transaction),
                })
            },
            (State::InTransaction(transaction), Transition::Commit) => {
                let _ = transaction.execute()?;
                Ok(Self {
                    root: self.root,
                    state: State::Idle,
                })
            },
            (State::InTransaction(_), Transition::Rollback) => {
                Ok(Self {
                    root: self.root,
                    state: State::Idle,
                })
            },
            (state, transition) => {
                Err(anyhow!("無効な状態遷移です: {state:?} -> {transition:?}"))
            }
        }
    }

    /// トランザクションを開始します。
    /// 
    /// # Errors
    /// - トランザクションの開始に失敗した場合
    #[must_use = "この関数は新しいManagerインスタンスを返します"]
    pub fn begin_transaction(self) -> Result<Self> {
        self.apply_transition(Transition::BeginTransaction)
    }

    /// トランザクションをコミットします。
    /// 
    /// # Errors
    /// - トランザクションのコミットに失敗した場合
    #[must_use = "この関数は新しいManagerインスタンスを返します"]
    pub fn commit(self) -> Result<Self> {
        self.apply_transition(Transition::Commit)
    }

    /// トランザクションをロールバックします。
    /// 
    /// # Errors
    /// - トランザクションのロールバックに失敗した場合
    #[must_use = "この関数は新しいManagerインスタンスを返します"]
    pub fn rollback(self) -> Result<Self> {
        self.apply_transition(Transition::Rollback)
    }

    /// ファイルの内容を読み込みます。
    /// 
    /// # Arguments
    /// * `path` - 読み込むファイルのパス
    /// 
    /// # Errors
    /// - パスの正規化に失敗した場合
    /// - ファイルが存在しない場合
    /// - ファイルの読み込みに失敗した場合
    #[must_use = "この関数はファイルの内容を返します"]
    pub fn read_file(&self, path: impl AsRef<Path>) -> Result<String> {
        let path = normalize(&*self.root, path)?;
        if !path.exists() {
            return Err(anyhow!("ファイルが見つかりません: {}", path.display()));
        }
        std::fs::read_to_string(&path)
            .map_err(|e| anyhow!("ファイルの読み込みに失敗しました: {e}"))
    }

    /// ファイルに内容を書き込みます。
    /// 
    /// # Arguments
    /// * `path` - 書き込み先のファイルパス
    /// * `content` - 書き込む内容
    /// 
    /// # Errors
    /// - パスの正規化に失敗した場合
    /// - トランザクションの操作に失敗した場合
    #[must_use = "この関数は新しいManagerインスタンスを返します"]
    pub fn write_file(self, path: impl AsRef<Path>, content: impl AsRef<str>) -> Result<Self> {
        let path = normalize(&*self.root, path)?;
        let operation = Arc::new(CreateFileOperation::new(path, content.as_ref().to_string()));
        
        match self.state {
            State::InTransaction(_) => {
                self.apply_transition(Transition::AddOperation(operation))
            },
            State::Idle => {
                self.begin_transaction()?
                    .apply_transition(Transition::AddOperation(operation))?
                    .commit()
            }
        }
    }

    /// ファイルを削除します。
    /// 
    /// # Arguments
    /// * `path` - 削除するファイルのパス
    /// 
    /// # Errors
    /// - パスの正規化に失敗した場合
    /// - トランザクションの操作に失敗した場合
    #[must_use = "この関数は新しいManagerインスタンスを返します"]
    pub fn delete_file(self, path: impl AsRef<Path>) -> Result<Self> {
        let path = normalize(&*self.root, path)?;
        let operation = Arc::new(DeleteFileOperation::new(path)?);
        
        match self.state {
            State::InTransaction(_) => {
                self.apply_transition(Transition::AddOperation(operation))
            },
            State::Idle => {
                self.begin_transaction()?
                    .apply_transition(Transition::AddOperation(operation))?
                    .commit()
            }
        }
    }

    /// ディレクトリを作成します。
    /// 
    /// # Arguments
    /// * `path` - 作成するディレクトリのパス
    /// 
    /// # Errors
    /// - パスの正規化に失敗した場合
    /// - ディレクトリの作成に失敗した場合
    /// - トランザクションの操作に失敗した場合
    #[must_use = "この関数は新しいManagerインスタンスを返します"]
    pub fn create_dir(self, path: impl AsRef<Path>) -> Result<Self> {
        let path = normalize(&*self.root, path)?;
        match self.state {
            State::InTransaction(_) => {
                let operation = Arc::new(CreateFileOperation::new(path, String::new()));
                self.apply_transition(Transition::AddOperation(operation))
            },
            State::Idle => {
                std::fs::create_dir_all(&path)
                    .map_err(|e| anyhow!("ディレクトリの作成に失敗しました: {e}"))?;
                Ok(self)
            }
        }
    }

    /// パスが存在するかどうかを確認します。
    /// 
    /// # Arguments
    /// * `path` - 確認するパス
    /// 
    /// # Errors
    /// - パスの正規化に失敗した場合
    #[must_use = "この関数はパスの存在を示すブール値を返します"]
    pub fn exists(&self, path: impl AsRef<Path>) -> Result<bool> {
        let path = normalize(&*self.root, path)?;
        Ok(path.exists())
    }

    /// ルートディレクトリのパスを取得します。
    #[must_use = "この関数はルートディレクトリのパスを返します"]
    pub fn root_path(&self) -> &Path {
        self.root.as_ref()
    }
} 