use std::sync::Arc;
use tokio::process::Command;
use anyhow::Result;
use crate::process::executor::Executor;
use crate::process::io::Buffer;
use std::time::Duration;

/// テストの実行を管理する構造体
#[derive(Debug)]
pub struct Runner {
    executor: Executor,
}

impl Default for Runner {
    fn default() -> Self {
        Self::new()
    }
}

impl Runner {
    /// 新しいテストランナーを作成する
    #[must_use]
    pub fn new() -> Self {
        Self {
            executor: Executor::new(),
        }
    }

    /// テストを実行する
    /// 
    /// # Arguments
    /// 
    /// * `source_file` - テスト対象のソースファイル
    /// * `input` - テストの入力データ
    /// * `timeout_secs` - タイムアウト時間（秒）
    /// * `memory_limit_mb` - メモリ制限（MB単位）
    /// 
    /// # Errors
    /// 
    /// * プロセスの実行に失敗した場合
    /// * タイムアウトが発生した場合
    /// * メモリ制限を超過した場合
    /// 
    /// # Panics
    /// 
    /// * タイムアウトテストでプロセスが正常終了した場合
    pub async fn run_test(&mut self, source_file: &str, input: &str, timeout_secs: u64, memory_limit_mb: Option<u64>) -> Result<String> {
        let buffer = Buffer::new(1024 * 1024); // 1MB buffer
        let command = Command::new(source_file);
        
        let mut process = self.executor.spawn(
            "test".to_string(),
            command,
            Arc::new(buffer),
            memory_limit_mb,
        ).await?;

        process.write_stdin(input.as_bytes()).await?;
        let status = process.wait_with_timeout(Duration::from_secs(timeout_secs)).await?;

        assert!(!status.exit_status.success(), "プロセスはタイムアウトで終了するはずです");
        
        Ok("テスト成功".to_string())
    }
} 