use anyhow::{Result, anyhow};
use rlimit::{setrlimit, Resource};
use std::fs::File;
use std::io::Read;

/// プロセスのリソース制限を管理するトレイト
pub trait Limits {
    /// メモリ制限を設定する
    /// 
    /// # Errors
    /// 
    /// * リソース制限の設定に失敗した場合
    fn set_memory_limit(&self, limit_bytes: u64) -> Result<()>;

    /// スタックサイズ制限を設定する
    /// 
    /// # Errors
    /// 
    /// * リソース制限の設定に失敗した場合
    fn set_stack_limit(&self, limit_bytes: u64) -> Result<()>;
}

impl Limits for std::process::Command {
    fn set_memory_limit(&self, limit_bytes: u64) -> Result<()> {
        setrlimit(
            Resource::AS,
            limit_bytes,
            limit_bytes,
        ).map_err(|e| anyhow!(
            "メモリ制限の設定に失敗しました: {e}"
        ))
    }

    fn set_stack_limit(&self, limit_bytes: u64) -> Result<()> {
        setrlimit(
            Resource::STACK,
            limit_bytes,
            limit_bytes,
        ).map_err(|e| anyhow!(
            "スタックサイズ制限の設定に失敗しました: {e}"
        ))
    }
}

/// メモリ制限を管理する構造体
#[derive(Debug, Clone, Copy)]
pub struct Memory {
    limit_bytes: u64,
}

impl Memory {
    /// 新しいメモリ制限を作成する
    /// 
    /// # Arguments
    /// 
    /// * `limit_mb` - メモリ制限（MB単位）
    #[must_use]
    pub const fn new(limit_mb: u64) -> Self {
        Self {
            limit_bytes: limit_mb * 1024 * 1024,
        }
    }

    /// メモリ制限を超過しているかチェックする
    /// 
    /// # Errors
    /// 
    /// * メモリ使用量の取得に失敗した場合
    pub fn is_exceeded(&self) -> Result<bool> {
        let mut status = String::new();
        File::open("/proc/self/status")?.read_to_string(&mut status)?;

        let rss = status.lines()
            .find(|line| line.starts_with("VmRSS:"))
            .and_then(|line| line.split_whitespace().nth(1))
            .and_then(|kb| kb.parse::<u64>().ok())
            .unwrap_or(0) * 1024;

        Ok(rss > self.limit_bytes)
    }
}

/// プロセスの状態を表す構造体
#[derive(Debug, Clone)]
pub struct Status {
    pub memory_exceeded: bool,
} 