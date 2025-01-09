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

    pub async fn execute(&self, configs: Vec<ContainerConfig>) -> Result<()> {
        let mut handles = vec![];
        
        for config in configs {
            let network = Arc::clone(&self.network);
            let buffer = Arc::clone(&self.buffer);
            let containers = Arc::clone(&self.containers);
            
            let handle = tokio::spawn(async move {
                let mut container = Container::new(config);
                {
                    let mut containers = containers.lock().await;
                    containers.push(container.clone());
                }
                container.run(network, buffer).await
            });
            
            handles.push(handle);
        }

        for handle in handles {
            handle.await.map_err(|e| anyhow!("タスク実行エラー: {}", e))??;
        }

        Ok(())
    }

    pub async fn cleanup(&self) -> Result<()> {
        let mut containers = self.containers.lock().await;
        for container in containers.iter_mut() {
            container.cleanup().await?;
        }
        containers.clear();
        Ok(())
    }
} 