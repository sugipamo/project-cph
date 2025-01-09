use std::sync::Arc;
use anyhow::{Result, anyhow};
use crate::container::{
    communication::ContainerNetwork,
    io::buffer::OutputBuffer,
};
use super::{container::Container, config::ContainerConfig};

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