use std::collections::HashMap;
use bytes::Bytes;
use tokio::sync::Mutex;
use anyhow::{Result, anyhow};

/// プロセスの出力を保持するバッファ
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
    pub async fn append(&self, process_id: &str, data: Bytes) -> Result<()> {
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
            let buffer = buffers.entry(process_id.to_string()).or_default();
            let current_size: usize = buffer.iter().map(Bytes::len).sum();
            
            if current_size + data_len <= self.max_buffer_size {
                buffer.push(data);
                Ok(())
            } else {
                Err(anyhow!("バッファサイズが制限を超えています"))
            }
        };

        // メモリ使用量を更新
        if buffer_result.is_ok() {
            let mut total_usage = self.total_memory_usage.lock().await;
            *total_usage += data_len;
        }

        buffer_result
    }

    /// バッファの内容を取得します
    pub async fn get(&self, process_id: &str) -> Option<Vec<Bytes>> {
        self.buffers.lock().await
            .get(process_id)
            .cloned()
    }

    /// バッファをクリアします
    pub async fn clear(&self, process_id: &str) {
        let mut buffers = self.buffers.lock().await;
        if let Some(buffer) = buffers.get_mut(process_id) {
            let freed_memory: usize = buffer.iter().map(Bytes::len).sum();
            buffer.clear();
            let mut total_usage = self.total_memory_usage.lock().await;
            *total_usage = total_usage.saturating_sub(freed_memory);
        }
    }
} 