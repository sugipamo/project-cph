use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{mpsc, Mutex};
use anyhow::{Result, anyhow};
use super::protocol::Message;

/// コンテナ間の通信を管理するネットワーク
#[derive(Default)]
pub struct Network {
    channels: Arc<Mutex<HashMap<String, mpsc::Sender<Message>>>>,
}

impl Network {
    /// 新しいネットワークを作成します
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// コンテナをネットワークに登録します
    ///
    /// # Errors
    /// - チャンネルの作成に失敗した場合
    pub async fn register(&self, container_id: &str) -> Result<(mpsc::Sender<Message>, mpsc::Receiver<Message>)> {
        let (tx, rx) = mpsc::channel(100);
        self.channels.lock().await.insert(container_id.to_string(), tx.clone());
        Ok((tx, rx))
    }

    pub async fn send(&self, _from: &str, to: &str, message: Message) -> Result<()> {
        let channels = self.channels.lock().await;
        if let Some(tx) = channels.get(to) {
            tx.send(message).await
                .map_err(|e| anyhow!("メッセージ送信に失敗: {}", e))?;
            Ok(())
        } else {
            Err(anyhow!("送信先コンテナが見つかりません: {}", to))
        }
    }

    pub async fn broadcast(&self, from: &str, message: Message) -> Result<()> {
        let channels = self.channels.lock().await;
        for (container_id, tx) in channels.iter() {
            if container_id != from {
                tx.send(message.clone()).await
                    .map_err(|e| anyhow!("ブロードキャスト送信に失敗: {}", e))?;
            }
        }
        Ok(())
    }

    pub async fn deregister(&self, container_id: &str) {
        self.channels.lock().await.remove(container_id);
    }
} 