use std::sync::Arc;
use tokio::process::Child;
use tokio::sync::Mutex;
use bytes::Bytes;
use anyhow::Result;

/// 入出力バッファを管理する構造体
#[derive(Debug)]
pub struct Buffer {
    data: Mutex<Vec<u8>>,
    max_size: usize,
}

impl Buffer {
    /// 新しいバッファを作成する
    /// 
    /// # Arguments
    /// 
    /// * `max_size` - バッファの最大サイズ（バイト単位）
    #[must_use]
    pub fn new(max_size: usize) -> Self {
        Self {
            data: Mutex::new(Vec::new()),
            max_size,
        }
    }

    /// バッファにデータを追加する
    /// 
    /// # Arguments
    /// 
    /// * `bytes` - 追加するデータ
    /// 
    /// # Errors
    /// 
    /// * バッファサイズの制限を超えた場合
    pub async fn append(&self, bytes: &[u8]) -> Result<()> {
        let mut data = self.data.lock().await;
        if data.len() + bytes.len() > self.max_size {
            anyhow::bail!("バッファサイズの制限を超えました");
        }
        data.extend_from_slice(bytes);
        drop(data);
        Ok(())
    }

    /// バッファの内容を取得する
    /// 
    /// # Errors
    /// 
    /// * バッファのロックに失敗した場合
    pub async fn get_contents(&self) -> Result<Bytes> {
        Ok(Bytes::from(self.data.lock().await.clone()))
    }

    /// バッファをクリアする
    /// 
    /// # Errors
    /// 
    /// * バッファのロックに失敗した場合
    pub async fn clear(&self) -> Result<()> {
        self.data.lock().await.clear();
        Ok(())
    }
}

/// 入出力を処理するハンドラ
#[derive(Debug)]
pub struct Handler {
    buffer: Arc<Buffer>,
}

impl Handler {
    /// 新しいハンドラを作成する
    /// 
    /// # Arguments
    /// 
    /// * `buffer` - 使用するバッファ
    #[must_use]
    pub const fn new(buffer: Arc<Buffer>) -> Self {
        Self { buffer }
    }

    /// 標準入力にデータを書き込む
    /// 
    /// # Arguments
    /// 
    /// * `child` - 子プロセス
    /// * `input` - 書き込むデータ
    /// 
    /// # Errors
    /// 
    /// * 書き込みに失敗した場合
    pub async fn write_stdin(child: &mut Child, input: &[u8]) -> Result<()> {
        if let Some(stdin) = child.stdin.as_mut() {
            use tokio::io::AsyncWriteExt;
            stdin.write_all(input).await?;
            stdin.flush().await?;
        }
        Ok(())
    }

    /// バッファを取得する
    #[must_use]
    pub fn get_buffer(&self) -> &Buffer {
        &self.buffer
    }

    /// バッファの最大サイズを取得する
    #[must_use]
    pub fn get_max_size(&self) -> usize {
        self.buffer.max_size
    }
} 