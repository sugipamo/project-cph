use std::collections::HashMap;
use bytes::Bytes;
use tokio::sync::Mutex;
use anyhow::{Result, anyhow};

pub struct OutputBuffer {
    buffers: Mutex<HashMap<String, Vec<Bytes>>>,
    max_buffer_size: usize,
}

impl OutputBuffer {
    pub fn new() -> Self {
        Self {
            buffers: Mutex::new(HashMap::new()),
            max_buffer_size: 1024 * 1024, // 1MB default
        }
    }

    pub fn with_max_size(max_size: usize) -> Self {
        Self {
            buffers: Mutex::new(HashMap::new()),
            max_buffer_size: max_size,
        }
    }

    pub async fn append(&self, container_id: &str, data: Bytes) -> Result<()> {
        let mut buffers = self.buffers.lock().await;
        let buffer = buffers.entry(container_id.to_string()).or_default();
        
        let current_size: usize = buffer.iter().map(|b| b.len()).sum();
        if current_size + data.len() <= self.max_buffer_size {
            buffer.push(data);
            Ok(())
        } else {
            Err(anyhow!("バッファが一杯です: {}", container_id))
        }
    }

    pub async fn get_output(&self, container_id: &str) -> Option<Vec<Bytes>> {
        self.buffers.lock().await
            .get(container_id)
            .cloned()
    }

    pub async fn clear(&self, container_id: &str) {
        if let Some(buffer) = self.buffers.lock().await.get_mut(container_id) {
            buffer.clear();
        }
    }

    pub async fn get_size(&self, container_id: &str) -> usize {
        self.buffers.lock().await
            .get(container_id)
            .map_or(0, |buffer| buffer.iter().map(|b| b.len()).sum())
    }
} 