use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{mpsc, Mutex};
use anyhow::{Result, anyhow};
use super::message::Message;

pub struct ContainerNetwork {
    channels: Arc<Mutex<HashMap<String, mpsc::Sender<Message>>>>,
}

impl ContainerNetwork {
    pub fn new() -> Self {
        Self {
            channels: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub async fn register(&self, container_id: &str) -> Result<(mpsc::Sender<Message>, mpsc::Receiver<Message>)> {
        let (tx, rx) = mpsc::channel(100);
        self.channels.lock().await.insert(container_id.to_string(), tx.clone());
        Ok((tx, rx))
    }

    pub async fn send(&self, from: &str, to: &str, message: Message) -> Result<()> {
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