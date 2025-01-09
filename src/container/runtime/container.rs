use std::sync::Arc;
use anyhow::Result;
use tokio::sync::oneshot;
use crate::container::{
    state::status::ContainerStatus,
    lifecycle::{LifecycleManager, LifecycleEvent},
    communication::{ContainerNetwork, Message},
    io::buffer::OutputBuffer,
};
use super::config::ContainerConfig;

pub struct Container {
    lifecycle: LifecycleManager,
    network: Option<Arc<ContainerNetwork>>,
    buffer: Option<Arc<OutputBuffer>>,
    cancel_tx: Option<oneshot::Sender<()>>,
}

impl Container {
    pub fn new(config: ContainerConfig) -> Self {
        Self {
            lifecycle: LifecycleManager::new(config),
            network: None,
            buffer: None,
            cancel_tx: None,
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
        self.lifecycle.handle_event(LifecycleEvent::Create).await?;
        self.lifecycle.handle_event(LifecycleEvent::Start).await?;

        // キャンセル用チャネル
        let (cancel_tx, mut cancel_rx) = oneshot::channel();
        self.cancel_tx = Some(cancel_tx);

        // メッセージ処理ループ
        loop {
            if self.lifecycle.status().is_terminal() {
                break;
            }

            tokio::select! {
                _ = &mut cancel_rx => {
                    break;
                }
            }
        }

        // クリーンアップ
        self.lifecycle.handle_event(LifecycleEvent::Stop).await?;
        self.lifecycle.handle_event(LifecycleEvent::Remove).await?;
        
        Ok(())
    }

    pub async fn cancel(&mut self) -> Result<()> {
        if let Some(tx) = self.cancel_tx.take() {
            let _ = tx.send(());
        }
        Ok(())
    }
}

impl Drop for Container {
    fn drop(&mut self) {
        if let Some(tx) = self.cancel_tx.take() {
            let _ = tx.send(());
        }
    }
} 