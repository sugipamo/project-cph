use anyhow::{Result, Context};
use rlimit::{Resource, setrlimit};

/// プロセスのリソース制限を設定します
pub trait ProcessLimits {
    fn set_memory_limit(&mut self, memory_mb: u64) -> &mut Self;
}

impl ProcessLimits for tokio::process::Command {
    fn set_memory_limit(&mut self, memory_mb: u64) -> &mut Self {
        let memory_bytes = memory_mb * 1024 * 1024;
        
        // プロセス生成前に実行される関数を設定
        unsafe {
            self.pre_exec(move || {
                // メモリ制限を設定
                setrlimit(
                    Resource::AS,  // 仮想メモリサイズ
                    memory_bytes,
                    memory_bytes
                ).map_err(|e| std::io::Error::new(
                    std::io::ErrorKind::Other,
                    format!("メモリ制限の設定に失敗しました: {}", e)
                ))?;

                // スタックサイズも制限
                setrlimit(
                    Resource::STACK,
                    memory_bytes / 8,
                    memory_bytes / 8
                ).map_err(|e| std::io::Error::new(
                    std::io::ErrorKind::Other,
                    format!("スタックサイズ制限の設定に失敗しました: {}", e)
                ))?;

                Ok(())
            });
        }
        self
    }
}

#[derive(Debug, Clone)]
pub struct MemoryMonitor {
    limit_bytes: u64,
}

impl MemoryMonitor {
    pub fn new(limit_mb: u64) -> Self {
        Self {
            limit_bytes: limit_mb * 1024 * 1024,
        }
    }

    pub fn is_exceeded(&self) -> Result<bool> {
        setrlimit(Resource::AS, self.limit_bytes, self.limit_bytes)
            .context("メモリ制限の設定に失敗しました")?;
        Ok(false)
    }
}

#[derive(Debug, Clone)]
pub struct ProcessStatus {
    pub memory_exceeded: bool,
} 