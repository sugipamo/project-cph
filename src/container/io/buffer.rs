use std::collections::HashMap;
use bytes::Bytes;
use tokio::sync::Mutex;
use anyhow::{Result, anyhow};

pub struct OutputBuffer {
    buffers: Mutex<HashMap<String, Vec<Bytes>>>,
    max_buffer_size: usize,
    total_memory_usage: Mutex<usize>,
}

impl OutputBuffer {
    pub fn new() -> Self {
        Self {
            buffers: Mutex::new(HashMap::new()),
            max_buffer_size: 1024 * 1024, // 1MB default
            total_memory_usage: Mutex::new(0),
        }
    }

    pub fn with_max_size(max_size: usize) -> Self {
        Self {
            buffers: Mutex::new(HashMap::new()),
            max_buffer_size: max_size,
            total_memory_usage: Mutex::new(0),
        }
    }

    pub async fn append(&self, container_id: &str, data: Bytes) -> Result<()> {
        let mut total_usage = self.total_memory_usage.lock().await;
        let data_len = data.len();

        // 全体のメモリ使用量をチェック
        if *total_usage + data_len > self.max_buffer_size * 10 {
            return Err(anyhow!("バッファの総メモリ使用量が制限を超えています"));
        }

        let mut buffers = self.buffers.lock().await;
        let buffer = buffers.entry(container_id.to_string()).or_default();
        
        let current_size: usize = buffer.iter().map(|b| b.len()).sum();
        if current_size + data_len <= self.max_buffer_size {
            buffer.push(data);
            *total_usage += data_len;
            Ok(())
        } else {
            Err(anyhow!("コンテナのバッファが一杯です: {}", container_id))
        }
    }

    pub async fn get_output(&self, container_id: &str) -> Option<Vec<Bytes>> {
        self.buffers.lock().await
            .get(container_id)
            .cloned()
    }

    pub async fn clear(&self, container_id: &str) {
        let mut buffers = self.buffers.lock().await;
        let mut total_usage = self.total_memory_usage.lock().await;

        if let Some(buffer) = buffers.get_mut(container_id) {
            let buffer_size: usize = buffer.iter().map(|b| b.len()).sum();
            *total_usage = total_usage.saturating_sub(buffer_size);
            buffer.clear();
        }
    }

    pub async fn get_size(&self, container_id: &str) -> usize {
        self.buffers.lock().await
            .get(container_id)
            .map_or(0, |buffer| buffer.iter().map(|b| b.len()).sum())
    }

    pub async fn get_total_memory_usage(&self) -> usize {
        *self.total_memory_usage.lock().await
    }

    pub async fn cleanup_old_data(&self, container_id: &str, max_entries: usize) -> Result<()> {
        let mut buffers = self.buffers.lock().await;
        let mut total_usage = self.total_memory_usage.lock().await;

        if let Some(buffer) = buffers.get_mut(container_id) {
            if buffer.len() > max_entries {
                let removed: usize = buffer.drain(..buffer.len() - max_entries)
                    .map(|b| b.len())
                    .sum();
                *total_usage = total_usage.saturating_sub(removed);
            }
        }

        Ok(())
    }
} 