use std::sync::Arc;
use anyhow::Result;
use chrono::Utc;
use tokio::sync::mpsc;
use crate::container::{
    state::lifecycle::ContainerStatus,
    communication::{ContainerNetwork, Message, StatusMessage, ControlMessage},
    io::buffer::OutputBuffer,
};

pub struct ContainerMessaging {
    container_id: String,
    network: Arc<ContainerNetwork>,
    buffer: Arc<OutputBuffer>,
    tx: mpsc::Sender<Message>,
    rx: mpsc::Receiver<Message>,
}

impl ContainerMessaging {
    pub async fn new(
        container_id: String,
        network: Arc<ContainerNetwork>,
        buffer: Arc<OutputBuffer>,
    ) -> Result<Self> {
        let (tx, rx) = network.register(&container_id).await?;
        
        Ok(Self {
            container_id,
            network,
            buffer,
            tx,
            rx,
        })
    }

    pub async fn send_status(&self, status: ContainerStatus) -> Result<()> {
        let message = Message::Status(StatusMessage {
            container_id: self.container_id.clone(),
            status,
            timestamp: Utc::now(),
        });
        self.network.broadcast(&self.container_id, message).await
    }

    pub async fn handle_message(&self, message: Message) -> Result<()> {
        match message {
            Message::Data(data) => {
                self.buffer.append(&self.container_id, data).await?;
            }
            Message::Control(control) => {
                self.handle_control(control).await?;
            }
            Message::Status(_) => {}
        }
        Ok(())
    }

    pub async fn handle_control(&self, _control: ControlMessage) -> Result<()> {
        // TODO: 制御メッセージの処理を実装
        Ok(())
    }

    pub async fn receive(&mut self) -> Option<Message> {
        self.rx.recv().await
    }
}

impl Drop for ContainerMessaging {
    fn drop(&mut self) {
        let container_id = self.container_id.clone();
        tokio::spawn(async move {
            // 非同期クリーンアップ処理
            if let Ok(()) = ContainerMessaging::cleanup(container_id).await {
                // クリーンアップ成功
            }
        });
    }
}

impl ContainerMessaging {
    async fn cleanup(container_id: String) -> Result<()> {
        // TODO: 必要なクリーンアップ処理を実装
        Ok(())
    }
} 