use tokio::io::{BufReader, AsyncBufReadExt, AsyncWriteExt};
use tokio::process::Child;
use bytes::Bytes;
use anyhow::{Result, bail};
use crate::process::io::Buffer;
use std::sync::Arc;

pub struct IoHandler {
    buffer: Arc<Buffer>,
}

impl IoHandler {
    pub fn new(buffer: Arc<Buffer>) -> Self {
        Self { buffer }
    }

    pub async fn setup_io(&self, child: &mut Child, process_id: &str) {
        if let Some(stdout) = child.stdout.take() {
            let buffer = self.buffer.clone();
            let process_id = process_id.to_string();
            tokio::spawn(async move {
                Self::handle_output(stdout, buffer.clone(), &process_id, "stdout").await;
                buffer.clear(&process_id).await;
            });
        }

        if let Some(stderr) = child.stderr.take() {
            let buffer = self.buffer.clone();
            let process_id = process_id.to_string();
            tokio::spawn(async move {
                Self::handle_output(stderr, buffer.clone(), &process_id, "stderr").await;
                buffer.clear(&process_id).await;
            });
        }
    }

    async fn handle_output<T: tokio::io::AsyncRead + Unpin>(
        output: T,
        buffer: Arc<Buffer>,
        process_id: &str,
        stream_name: &str,
    ) {
        let mut reader = BufReader::new(output);
        let mut line = String::new();
        while let Ok(n) = reader.read_line(&mut line).await {
            if n == 0 { break; }
            if let Err(e) = buffer.append(process_id, Bytes::from(line.clone())).await {
                eprintln!("{} バッファリングエラー: {}", stream_name, e);
            }
            line.clear();
        }
    }

    pub async fn write_stdin(child: &mut Child, input: &str) -> Result<()> {
        if let Some(stdin) = child.stdin.as_mut() {
            stdin.write_all(input.as_bytes()).await?;
            stdin.flush().await?;
            Ok(())
        } else {
            bail!("プロセスの標準入力が利用できません");
        }
    }

    pub async fn read_output(&self, process_id: &str) -> Option<Vec<Bytes>> {
        self.buffer.get(process_id).await
    }

    pub async fn cleanup(&self, process_id: &str) {
        self.buffer.clear(process_id).await;
    }
} 