use anyhow::Result;
use bytes::Bytes;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::process::Child;
use tokio::io::AsyncWriteExt;

#[derive(Debug, Clone)]
pub struct Buffer {
    data: Arc<Mutex<Vec<u8>>>,
    max_size: usize,
}

impl Buffer {
    pub fn new(max_size: usize) -> Self {
        Self {
            data: Arc::new(Mutex::new(Vec::new())),
            max_size,
        }
    }

    pub async fn append(&self, bytes: &[u8]) -> Result<()> {
        let mut data = self.data.lock().await;
        if data.len() + bytes.len() > self.max_size {
            anyhow::bail!("バッファサイズの制限を超えました");
        }
        data.extend_from_slice(bytes);
        Ok(())
    }

    pub async fn get_contents(&self) -> Result<Bytes> {
        let data = self.data.lock().await;
        Ok(Bytes::copy_from_slice(&data))
    }

    pub async fn clear(&self) -> Result<()> {
        let mut data = self.data.lock().await;
        data.clear();
        Ok(())
    }
}

#[derive(Debug, Clone)]
pub struct IoHandler {
    buffer: Arc<Buffer>,
}

impl IoHandler {
    pub fn new(buffer: Arc<Buffer>) -> Self {
        Self { buffer }
    }

    pub async fn write_stdin(child: &mut Child, input: &[u8]) -> Result<()> {
        if let Some(stdin) = child.stdin.as_mut() {
            stdin.write_all(input).await?;
            stdin.flush().await?;
        }
        Ok(())
    }

    pub fn get_buffer(&self) -> &Buffer {
        &self.buffer
    }

    pub fn get_max_size(&self) -> usize {
        self.buffer.max_size
    }
} 