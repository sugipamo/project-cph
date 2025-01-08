use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Type {
    Running,
    Executing(String),
    Stopped,
    Failed(String),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Info {
    pub container_id: String,
    pub state_type: Type,
}

impl Info {
    #[must_use]
    pub const fn new(container_id: String, state_type: Type) -> Self {
        Self {
            container_id,
            state_type,
        }
    }
}

impl fmt::Display for Info {
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