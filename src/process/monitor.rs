use std::os::unix::process::ExitStatusExt;
use std::process::ExitStatus;
use std::time::Duration;
use tokio::time;
use tokio::process::Child;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::fs::File;
use std::io::Read;
use anyhow::Context;

/// プロセスの終了状態を表す構造体
#[derive(Debug, Clone)]
pub struct Status {
    pub exit_status: ExitStatus,
    pub memory_exceeded: bool,
}

/// プロセスの監視を行う構造体
#[derive(Debug, Clone)]
pub struct Monitor {
    memory_limit_mb: Option<u64>,
    child: Arc<Mutex<Child>>,
}

impl Monitor {
    /// 新しいモニターを作成する
    /// 
    /// # Arguments
    /// 
    /// * `memory_limit_mb` - メモリ制限（MB単位）。Noneの場合は制限なし
    /// * `child` - 監視対象の子プロセス
    #[must_use]
    pub const fn new(memory_limit_mb: Option<u64>, child: Arc<Mutex<Child>>) -> Self {
        Self { memory_limit_mb, child }
    }

    /// プロセスのメモリ使用量を取得する（KB単位）
    /// 
    /// # Errors
    /// 
    /// * プロセスIDの取得に失敗した場合
    /// * プロセスの状態ファイルの読み取りに失敗した場合
    /// * メモリ使用量の解析に失敗した場合
    async fn get_memory_usage_kb(&self) -> anyhow::Result<u64> {
        let pid = {
            let child = self.child.lock().await;
            child.id().context("Failed to get process ID")?
        };
        let status_file = format!("/proc/{pid}/status");
        let mut content = String::new();
        File::open(status_file)?.read_to_string(&mut content)?;

        // VmRSSとVmSwapの値を取得
        let vm_rss = Self::parse_memory_value(&content, "VmRSS:")?;
        let vm_swap = Self::parse_memory_value(&content, "VmSwap:").unwrap_or(0);

        Ok(vm_rss + vm_swap)
    }

    /// プロセスの状態ファイルからメモリ値を解析する
    /// 
    /// # Errors
    /// 
    /// * 指定された値が見つからない場合
    /// * 値の解析に失敗した場合
    fn parse_memory_value(content: &str, prefix: &str) -> anyhow::Result<u64> {
        let line = content.lines()
            .find(|line| line.starts_with(prefix))
            .context(format!("Failed to find {prefix} in status file"))?;
        
        let value = line.split_whitespace()
            .nth(1)
            .context(format!("Failed to parse {prefix} value"))?
            .parse::<u64>()?;
        
        Ok(value)
    }

    /// メモリ制限を超過しているかどうかを確認する
    async fn check_memory_limit(&self) -> bool {
        if let Some(limit_mb) = self.memory_limit_mb {
            if let Ok(usage_kb) = self.get_memory_usage_kb().await {
                return usage_kb > limit_mb * 1024;
            }
        }
        false
    }

    /// タイムアウト付きでプロセスの終了を待機する
    /// 
    /// # Arguments
    /// 
    /// * `timeout` - タイムアウト時間
    /// * `kill_fn` - プロセスを強制終了するための関数
    /// 
    /// # Errors
    /// 
    /// * プロセスの終了待機に失敗した場合
    /// * プロセスの強制終了に失敗した場合
    pub async fn wait_with_timeout<F, Fut>(&self, timeout: Duration, kill_fn: F) -> Status
    where
        F: FnOnce() -> Fut + Clone + Send + 'static,
        Fut: std::future::Future<Output = anyhow::Result<()>> + Send,
    {
        let memory_check = async {
            while !self.check_memory_limit().await {
                time::sleep(Duration::from_millis(100)).await;
            }
        };

        let kill_fn2 = kill_fn.clone();
        let result = tokio::select! {
            result = self.wait() => result,
            () = memory_check => {
                let _ = kill_fn().await;
                Ok(ExitStatus::from_raw(137)) // OOM killer signal
            }
        };

        match time::timeout(timeout, async { result }).await {
            Ok(Ok(status)) => Status {
                exit_status: status,
                memory_exceeded: status.code() == Some(137),
            },
            Ok(Err(_)) => Status {
                exit_status: ExitStatus::from_raw(1),
                memory_exceeded: false,
            },
            Err(_) => {
                let _ = kill_fn2().await;
                Status {
                    exit_status: ExitStatus::from_raw(124),
                    memory_exceeded: false,
                }
            }
        }
    }

    /// プロセスの終了を待機する
    /// 
    /// # Errors
    /// 
    /// * プロセスの終了待機に失敗した場合
    async fn wait(&self) -> anyhow::Result<ExitStatus> {
        let mut child = self.child.lock().await;
        Ok(child.wait().await?)
    }
} 