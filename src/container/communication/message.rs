use serde::{Deserialize, Serialize};
use std::time::SystemTime;

/// コンテナ間で送受信されるメッセージの標準フォーマット
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    /// メッセージID
    pub id: String,
    /// 送信元コンテナID
    pub from: String,
    /// 宛先コンテナID（ブロードキャストの場合はNone）
    pub to: Option<String>,
    /// メッセージの種類
    pub kind: MessageKind,
    /// メッセージの内容
    pub content: String,
    /// タイムスタンプ
    pub timestamp: SystemTime,
    /// メッセージの優先度
    pub priority: Priority,
}

/// メッセージの種類
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MessageKind {
    /// 通常のメッセージ
    Normal,
    /// システムメッセージ（コンテナの状態変更など）
    System,
    /// エラーメッセージ
    Error,
    /// デバッグメッセージ
    Debug,
}

/// メッセージの優先度
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum Priority {
    Low,
    Normal,
    High,
    Critical,
}

impl Message {
    /// 新しいメッセージを作成
    pub fn new(
        from: String,
        to: Option<String>,
        content: String,
        kind: MessageKind,
        priority: Priority,
    ) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            from,
            to,
            kind,
            content,
            timestamp: SystemTime::now(),
            priority,
        }
    }

    /// 通常メッセージを作成
    pub fn normal(from: String, to: String, content: String) -> Self {
        Self::new(
            from,
            Some(to),
            content,
            MessageKind::Normal,
            Priority::Normal,
        )
    }

    /// システムメッセージを作成
    pub fn system(from: String, content: String) -> Self {
        Self::new(
            from,
            None,
            content,
            MessageKind::System,
            Priority::High,
        )
    }

    /// エラーメッセージを作成
    pub fn error(from: String, content: String) -> Self {
        Self::new(
            from,
            None,
            content,
            MessageKind::Error,
            Priority::Critical,
        )
    }

    /// デバッグメッセージを作成
    pub fn debug(from: String, content: String) -> Self {
        Self::new(
            from,
            None,
            content,
            MessageKind::Debug,
            Priority::Low,
        )
    }

    /// ブロードキャストメッセージを作成
    pub fn broadcast(from: String, content: String) -> Self {
        Self::new(
            from,
            None,
            content,
            MessageKind::Normal,
            Priority::Normal,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_message_creation() {
        let msg = Message::normal(
            "container1".to_string(),
            "container2".to_string(),
            "Hello".to_string(),
        );
        assert_eq!(msg.kind, MessageKind::Normal);
        assert_eq!(msg.priority, Priority::Normal);
        assert_eq!(msg.from, "container1");
        assert_eq!(msg.to, Some("container2".to_string()));
    }

    #[test]
    fn test_system_message() {
        let msg = Message::system(
            "container1".to_string(),
            "Started".to_string(),
        );
        assert_eq!(msg.kind, MessageKind::System);
        assert_eq!(msg.priority, Priority::High);
        assert_eq!(msg.to, None);
    }

    #[test]
    fn test_broadcast_message() {
        let msg = Message::broadcast(
            "container1".to_string(),
            "Broadcast message".to_string(),
        );
        assert_eq!(msg.kind, MessageKind::Normal);
        assert_eq!(msg.to, None);
    }
} 