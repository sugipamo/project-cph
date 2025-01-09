use std::sync::Arc;
use anyhow::Result;
use tokio::sync::oneshot;
use crate::container::{
    state::status::ContainerStatus,
    communication::{ContainerNetwork, Message},
    io::buffer::OutputBuffer,
};
use super::config::ContainerConfig;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LifecycleEvent {
    Create,
    Start,
    Stop,
    Remove,
}

pub struct Container {
    network: Option<Arc<ContainerNetwork>>,
    buffer: Option<Arc<OutputBuffer>>,
    cancel_tx: Option<oneshot::Sender<()>>,
    config: ContainerConfig,
    container_id: Option<String>,
    status: ContainerStatus,
}

impl Container {
    pub fn new(config: ContainerConfig) -> Self {
        Self {
            network: None,
            buffer: None,
            cancel_tx: None,
            config,
            container_id: None,
            status: ContainerStatus::Created,
        }
    }

    pub async fn run(
        &mut self,
        network: Arc<ContainerNetwork>,
        buffer: Arc<OutputBuffer>,
    ) -> Result<()> {
        self.network = Some(network.clone());
        self.buffer = Some(buffer.clone());

        // コンテナの作成と起動
        self.handle_lifecycle_event(LifecycleEvent::Create).await?;
        self.handle_lifecycle_event(LifecycleEvent::Start).await?;

        // キャンセル用チャネル
        let (cancel_tx, mut cancel_rx) = oneshot::channel();
        self.cancel_tx = Some(cancel_tx);

        // メッセージ処理ループ
        loop {
            if self.status.is_terminal() {
                break;
            }

            tokio::select! {
                _ = &mut cancel_rx => {
                    break;
                }
            }
        }

        // クリーンアップ
        self.handle_lifecycle_event(LifecycleEvent::Stop).await?;
        self.handle_lifecycle_event(LifecycleEvent::Remove).await?;
        
        Ok(())
    }

    pub async fn cancel(&mut self) -> Result<()> {
        if let Some(tx) = self.cancel_tx.take() {
            let _ = tx.send(());
        }
        Ok(())
    }

    pub async fn handle_lifecycle_event(&mut self, event: LifecycleEvent) -> Result<ContainerStatus> {
        match event {
            LifecycleEvent::Create => self.create().await?,
            LifecycleEvent::Start => self.start().await?,
            LifecycleEvent::Stop => self.stop().await?,
            LifecycleEvent::Remove => self.remove().await?,
        }
        Ok(self.status.clone())
    }

    pub fn id(&self) -> Option<&str> {
        self.container_id.as_deref()
    }

    pub fn status(&self) -> &ContainerStatus {
        &self.status
    }
}

impl Drop for Container {
    fn drop(&mut self) {
        if let Some(tx) = self.cancel_tx.take() {
            let _ = tx.send(());
        }
    }
} 