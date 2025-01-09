use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::mpsc;
use tokio::process::Command;
use anyhow::{Result, anyhow};
use crate::container::{
    ContainerError, ContainerStatus,
    network::{ContainerNetwork, Message, StatusMessage, ControlMessage},
    buffer::OutputBuffer,
};
use chrono::Utc;

#[derive(Debug, Clone)]
pub struct ContainerConfig {
    pub id: String,
    pub image: String,
    pub working_dir: PathBuf,
    pub command: Vec<String>,
    pub env_vars: Vec<String>,
}

pub struct Container {
    config: ContainerConfig,
    container_id: Option<String>,
}

impl Container {
    pub fn new(config: ContainerConfig) -> Self {
        Self {
            config,
            container_id: None,
        }
    }

    pub async fn run(
        &mut self,
        network: Arc<ContainerNetwork>,
        buffer: Arc<OutputBuffer>,
    ) -> Result<()> {
        self.create_container().await?;
        let (tx, mut rx) = network.register(&self.config.id).await
            .map_err(|e| anyhow!("ネットワーク登録に失敗: {}", e))?;
        
        self.send_status(&network, ContainerStatus::Running).await?;
        
        while let Some(message) = rx.recv().await {
            match message {
                Message::Data(data) => {
                    buffer.append(&self.config.id, data).await
                        .map_err(|e| anyhow!("バッファ追加に失敗: {}", e))?;
                }
                Message::Control(control) => {
                    self.handle_control(control).await?;
                }
                Message::Status(_) => {}
            }
        }
        
        Ok(())
    }

    async fn create_container(&mut self) -> Result<()> {
        let output = Command::new("docker")
            .args([
                "create",
                "--rm",
                "-w", self.config.working_dir.to_str().unwrap_or("/"),
            ])
            .args(&self.config.env_vars.iter().flat_map(|env| vec!["-e", env]))
            .arg(&self.config.image)
            .args(&self.config.command)
            .output()
            .await
            .map_err(|e| anyhow!("コンテナ作成に失敗: {}", e))?;

        if !output.status.success() {
            return Err(anyhow!(
                "コンテナ作成エラー: {}",
                String::from_utf8_lossy(&output.stderr)
            ));
        }

        let container_id = String::from_utf8(output.stdout)
            .map_err(|e| anyhow!("コンテナID解析に失敗: {}", e))?
            .trim()
            .to_string();

        self.container_id = Some(container_id);
        Ok(())
    }

    async fn send_status(&self, network: &ContainerNetwork, status: ContainerStatus) -> Result<()> {
        let message = Message::Status(StatusMessage {
            container_id: self.config.id.clone(),
            status,
            timestamp: Utc::now(),
        });
        network.broadcast(&self.config.id, message).await
            .map_err(|e| anyhow!("ステータス送信に失敗: {}", e))
    }

    async fn handle_control(&mut self, _control: ControlMessage) -> Result<()> {
        // TODO: 制御メッセージの処理を実装
        Ok(())
    }
}

pub struct ParallelExecutor {
    network: Arc<ContainerNetwork>,
    buffer: Arc<OutputBuffer>,
}

impl ParallelExecutor {
    pub fn new() -> Self {
        Self {
            network: Arc::new(ContainerNetwork::new()),
            buffer: Arc::new(OutputBuffer::new()),
        }
    }

    pub async fn execute(&self, configs: Vec<ContainerConfig>) -> Result<()> {
        let mut handles = vec![];
        
        for config in configs {
            let network = Arc::clone(&self.network);
            let buffer = Arc::clone(&self.buffer);
            
            let handle = tokio::spawn(async move {
                let mut container = Container::new(config);
                container.run(network, buffer).await
            });
            
            handles.push(handle);
        }

        for handle in handles {
            handle.await.map_err(|e| anyhow!("タスク実行エラー: {}", e))??;
        }

        Ok(())
    }
} 