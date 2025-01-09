use std::sync::Arc;
use anyhow::Result;
use tokio::sync::oneshot;
use crate::container::{
    state::lifecycle::ContainerStatus,
    communication::{ContainerNetwork, Message},
    io::buffer::OutputBuffer,
};
use super::{
    config::ContainerConfig,
    lifecycle::ContainerLifecycle,
    messaging::ContainerMessaging,
};

pub struct Container {
    lifecycle: ContainerLifecycle,
    messaging: Option<ContainerMessaging>,
    cancel_tx: Option<oneshot::Sender<()>>,
}

impl Container {
    pub fn new(config: ContainerConfig) -> Self {
        Self {
            lifecycle: ContainerLifecycle::new(config),
            messaging: None,
            cancel_tx: None,
        }
    }

    pub async fn run(
        &mut self,
        network: Arc<ContainerNetwork>,
        buffer: Arc<OutputBuffer>,
    ) -> Result<()> {
        // コンテナの作成
        self.lifecycle.create().await?;

        // メッセージング設定
        let container_id = self.lifecycle.id()
            .ok_or_else(|| anyhow::anyhow!("コンテナIDが見つかりません"))?
            .to_string();
        
        let mut messaging = ContainerMessaging::new(
            container_id,
            network,
            buffer,
        ).await?;

        // ステータス通知
        messaging.send_status(ContainerStatus::Running).await?;

        // キャンセル用チャネル
        let (cancel_tx, mut cancel_rx) = oneshot::channel();
        self.cancel_tx = Some(cancel_tx);

        // コンテナ起動
        self.lifecycle.start().await?;

        // メッセージ処理ループ
        loop {
            tokio::select! {
                message = messaging.receive() => {
                    match message {
                        Some(msg) => messaging.handle_message(msg).await?,
                        None => break,
                    }
                }
                _ = &mut cancel_rx => {
                    break;
                }
            }
        }

        // クリーンアップ
        self.lifecycle.stop().await?;
        self.lifecycle.remove().await?;
        
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