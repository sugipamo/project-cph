use std::os::unix::process::CommandExt;
use rlimit::{Resource, Rlimit, setrlimit};
use anyhow::{Result, Context};

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
                    Resource::RLIMIT_AS,  // 仮想メモリサイズ
                    Rlimit::new(memory_bytes, memory_bytes)
                ).map_err(|e| std::io::Error::new(
                    std::io::ErrorKind::Other,
                    format!("メモリ制限の設定に失敗しました: {}", e)
                ))?;

                // スタックサイズも制限
                setrlimit(
                    Resource::RLIMIT_STACK,
                    Rlimit::new(memory_bytes / 8, memory_bytes / 8)
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

/// プロセスのメモリ使用量を監視します
#[derive(Debug)]
pub struct MemoryMonitor {
    pid: u32,
    limit_bytes: u64,
}

impl MemoryMonitor {
    pub fn new(pid: u32, limit_mb: u64) -> Self {
        Self {
            pid,
            limit_bytes: limit_mb * 1024 * 1024,
        }
    }

    /// 現在のメモリ使用量を取得します（バイト単位）
    pub fn get_memory_usage(&self) -> Result<u64> {
        let path = format!("/proc/{}/statm", self.pid);
        let contents = std::fs::read_to_string(&path)
            .context("プロセスのメモリ情報の読み取りに失敗しました")?;
        
        let pages = contents
            .split_whitespace()
            .next()
            .ok_or_else(|| anyhow::anyhow!("メモリ情報の解析に失敗しました"))?
            .parse::<u64>()
            .context("メモリ使用量の解析に失敗しました")?;
        
        Ok(pages * 4096) // ページサイズは4KBと仮定
    }

    /// メモリ制限を超過しているかチェックします
    pub fn is_exceeded(&self) -> Result<bool> {
        let usage = self.get_memory_usage()?;
        Ok(usage > self.limit_bytes)
    }
} 