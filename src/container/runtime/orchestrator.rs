use std::sync::Arc;
use anyhow::{Result, anyhow};
use tokio::sync::Mutex;
use crate::container::{
    communication::ContainerNetwork,
    io::buffer::OutputBuffer,
};
use super::{container::Container, config::ContainerConfig};

pub struct ParallelExecutor {
    network: Arc<ContainerNetwork>,
    buffer: Arc<OutputBuffer>,
    containers: Arc<Mutex<Vec<Container>>>,
}

impl ParallelExecutor {
    pub fn new() -> Self {
        Self {
            network: Arc::new(ContainerNetwork::new()),
            buffer: Arc::new(OutputBuffer::new()),
            containers: Arc::new(Mutex::new(Vec::new())),
        }
    }

    async fn add_container(&self, container: Container) -> Result<()> {
        let mut containers = self.containers.lock().await;
        containers.push(container);
        Ok(())
    }

    pub async fn execute(&self, configs: Vec<ContainerConfig>) -> Result<()> {
        let mut handles = vec![];
        
        for config in configs {
            let network = Arc::clone(&self.network);
            let buffer = Arc::clone(&self.buffer);
            let containers_ref = Arc::clone(&self.containers);
            
            let handle = tokio::spawn(async move {
                let container = Container::new(config, network, buffer).await?;
                
                // コンテナの追加は最小限のロック時間で行う
                {
                    let mut containers = containers_ref.lock().await;
                    containers.push(container.clone());
                }
                
                container.run().await
            });
            
            handles.push(handle);
        }

        for handle in handles {
            handle.await.map_err(|e| anyhow!("タスク実行エラー: {}", e))??;
        }

        Ok(())
    }

    pub async fn cleanup(&self) -> Result<()> {
        let containers = {
            let mut containers = self.containers.lock().await;
            std::mem::take(&mut *containers)
        };

        for mut container in containers {
            container.cleanup().await?;
        }
        
        Ok(())
    }
} 