use std::collections::HashMap;
use bytes::Bytes;
use tokio::sync::Mutex;
use anyhow::{Result, anyhow};

/// コンテナの出力を保持するバッファ
#[derive(Default)]
pub struct Buffer {
    buffers: Mutex<HashMap<String, Vec<Bytes>>>,
    max_buffer_size: usize,
    total_memory_usage: Mutex<usize>,
}

impl Buffer {
    /// 新しいバッファを作成します
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// 指定したサイズ制限でバッファを作成します
    #[must_use]
    pub fn with_max_size(max_size: usize) -> Self {
        Self {
            max_buffer_size: max_size,
            ..Default::default()
        }
    }

    /// データをバッファに追加します
    ///
    /// # Errors
    /// - バッファのサイズ制限を超えた場合
    pub async fn append(&self, container_id: &str, data: Bytes) -> Result<()> {
        let data_len = data.len();

        // 全体のメモリ使用量をチェック
        {
            let total_usage = self.total_memory_usage.lock().await;
            if *total_usage + data_len > self.max_buffer_size * 10 {
                return Err(anyhow!("バッファの総メモリ使用量が制限を超えています"));
            }
        }

        let buffer_result = {
            let mut buffers = self.buffers.lock().await;
            let buffer = buffers.entry(container_id.to_string()).or_default();
            let current_size: usize = buffer.iter().map(Bytes::len).sum();
            
            if current_size + data_len <= self.max_buffer_size {
                buffer.push(data);
                drop(buffers);  // 早期にロックを解放
                Ok(data_len)
            } else {
                drop(buffers);  // 早期にロックを解放
                Err(anyhow!("コンテナのバッファが一杯です: {}", container_id))
            }
        };

        if let Ok(added_size) = buffer_result {
            let mut total_usage = self.total_memory_usage.lock().await;
            *total_usage += added_size;
        }

        buffer_result.map(|_| ())
    }

    pub async fn get_output(&self, container_id: &str) -> Option<Vec<Bytes>> {
        self.buffers.lock().await
            .get(container_id)
            .cloned()
    }

    pub async fn clear(&self, container_id: &str) {
        let buffer_size = {
            let buffers = self.buffers.lock().await;
            buffers.get(container_id)
                .map_or(0, |buffer| buffer.iter().map(Bytes::len).sum())
        };

        if buffer_size > 0 {
            let mut total_usage = self.total_memory_usage.lock().await;
            *total_usage = total_usage.saturating_sub(buffer_size);
            drop(total_usage);

            let mut buffers = self.buffers.lock().await;
            if let Some(buffer) = buffers.get_mut(container_id) {
                buffer.clear();
            }
        }
    }

    pub async fn get_size(&self, container_id: &str) -> usize {
        self.buffers.lock().await
            .get(container_id)
            .map_or(0, |buffer| buffer.iter().map(Bytes::len).sum())
    }

    pub async fn get_total_memory_usage(&self) -> usize {
        *self.total_memory_usage.lock().await
    }

    /// 古いデータをクリーンアップします。
    ///
    /// # Errors
    /// - バッファの操作に失敗した場合
    pub async fn cleanup_old_data(&self, container_id: &str, max_entries: usize) -> Result<()> {
        let removed_size = {
            let mut buffers = self.buffers.lock().await;
            buffers.get_mut(container_id).map_or(0, |buffer| {
                if buffer.len() > max_entries {
                    buffer.drain(..buffer.len() - max_entries)
                        .map(|b| b.len())
                        .sum()
                } else {
                    0
                }
            })
        };

        if removed_size > 0 {
            let mut total_usage = self.total_memory_usage.lock().await;
            *total_usage = total_usage.saturating_sub(removed_size);
        }

        Ok(())
    }
} 