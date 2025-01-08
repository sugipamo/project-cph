use std::fmt;

/// コンテ�の状態を表す列挙型
///
/// # Variants
/// * `Running` - コンテナが実行中
/// * `Executing` - コンテナでコマンドを実行中（コマンド文字列を保持）
/// * `Stopped` - コンテナが停止済み
/// * `Failed` - コンテナが失敗（エラーメッセージを保持）
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Type {
    Running,
    Executing(String),
    Stopped,
    Failed(String),
}

/// コンテナの状態情報を保持する構造体
///
/// # Fields
/// * `container_id` - コンテナのID
/// * `state_type` - コンテナの状態
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Info {
    pub container_id: String,
    pub state_type: Type,
}

impl Info {
    /// 新しい状態情報インスタンスを作成します
    ///
    /// # Arguments
    /// * `container_id` - コンテナのID
    /// * `state_type` - コンテナの状態
    ///
    /// # Returns
    /// * `Self` - 新しい状態情報インスタンス
    #[must_use = "この関数は新しい状態情報インスタンスを返します"]
    pub const fn new(container_id: String, state_type: Type) -> Self {
        Self {
            container_id,
            state_type,
        }
    }
}

impl fmt::Display for Info {
    /// 状態情報を文字列として整形します
    ///
    /// # Arguments
    /// * `f` - フォーマッタ
    ///
    /// # Returns
    /// * `fmt::Result` - 文字列フォーマット結果
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match &self.state_type {
            Type::Running => {
                write!(f, "実行中(ID: {container_id})", container_id = self.container_id)
            }
            Type::Executing(command) => {
                write!(f, "コマンド実行中(ID: {container_id}, コマンド: {command})", container_id = self.container_id)
            }
            Type::Stopped => {
                write!(f, "停止済み(ID: {container_id})", container_id = self.container_id)
            }
            Type::Failed(error) => {
                write!(f, "失敗(ID: {container_id}, エラー: {error})", container_id = self.container_id)
            }
        }
    }
} 