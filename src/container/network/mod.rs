use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{mpsc, Mutex};
use bytes::Bytes;
use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc};
use crate::container::{ContainerError, ContainerStatus, Result};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Message {
    Data(Bytes),
    Control(ControlMessage),
    Status(StatusMessage),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ControlMessage {
    Start,
    Stop,
    Pause,
    Resume,
    Custom(String, Bytes),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatusMessage {
    pub container_id: String,
    pub status: ContainerStatus,
    pub timestamp: DateTime<Utc>,
}

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
                .map_err(|e| ContainerError::Communication(e.to_string()))?;
            Ok(())
        } else {
            Err(ContainerError::Communication(format!("送信先コンテナが見つかりません: {}", to)))
        }
    }

    pub async fn broadcast(&self, from: &str, message: Message) -> Result<()> {
        let channels = self.channels.lock().await;
        for (container_id, tx) in channels.iter() {
            if container_id != from {
                tx.send(message.clone()).await
                    .map_err(|e| ContainerError::Communication(e.to_string()))?;
            }
        }
        Ok(())
    }

    pub async fn deregister(&self, container_id: &str) {
        self.channels.lock().await.remove(container_id);
    }
} 