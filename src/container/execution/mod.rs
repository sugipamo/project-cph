use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::mpsc;
use tokio::process::Command;
use crate::container::{
    ContainerError, ContainerStatus, Result,
    network::{ContainerNetwork, Message, StatusMessage},
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
        // コンテナの作成と起動
        self.create_container().await?;
        
        let (tx, mut rx) = network.register(&self.config.id).await?;
        
        // ステータス更新
        self.send_status(&network, ContainerStatus::Running).await?;
        
        // メッセージ処理ループ
        while let Some(message) = rx.recv().await {
            match message {
                Message::Data(data) => {
                    buffer.append(&self.config.id, data).await?;
                }
                Message::Control(control) => {
                    self.handle_control(control).await?;
                }
                Message::Status(_) => {} // ステータスメッセージは無視
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
            .map_err(|e| ContainerError::Creation(e.to_string()))?;

        if !output.status.success() {
            return Err(ContainerError::Creation(
                String::from_utf8_lossy(&output.stderr).to_string()
            ));
        }

        let container_id = String::from_utf8(output.stdout)
            .map_err(|e| ContainerError::Creation(e.to_string()))?
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
            handle.await.map_err(|e| ContainerError::Internal(e.to_string()))??;
        }

        Ok(())
    }
} 