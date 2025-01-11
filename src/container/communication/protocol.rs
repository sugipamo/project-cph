use std::time::SystemTime;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum MessageKind {
    Normal,
    System,
    Error,
    Debug,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Message {
    pub id: String,
    pub from: String,
    pub to: String,
    pub kind: MessageKind,
    pub content: String,
    pub timestamp: SystemTime,
}

impl Message {
    pub fn new(content: impl Into<String>, from: impl Into<String>, to: impl Into<String>, kind: MessageKind) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            from: from.into(),
            to: to.into(),
            kind,
            content: content.into(),
            timestamp: SystemTime::now(),
        }
    }

    pub fn normal(content: impl Into<String>, from: impl Into<String>, to: impl Into<String>) -> Self {
        Self::new(content, from, to, MessageKind::Normal)
    }

    pub fn system(content: impl Into<String>, from: impl Into<String>, to: impl Into<String>) -> Self {
        Self::new(content, from, to, MessageKind::System)
    }

    pub fn error(content: impl Into<String>, from: impl Into<String>, to: impl Into<String>) -> Self {
        Self::new(content, from, to, MessageKind::Error)
    }

    pub fn debug(content: impl Into<String>, from: impl Into<String>, to: impl Into<String>) -> Self {
        Self::new(content, from, to, MessageKind::Debug)
    }
} 