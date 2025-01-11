use cph::container::runtime::Runtime;
use cph::container::runtime::config::Config;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use std::sync::Arc;
use tokio::sync::Mutex;

pub struct MockRuntime {
    should_fail: bool,
    is_running: Arc<Mutex<bool>>,
}

impl MockRuntime {
    pub fn new() -> Self {
        Self {
            should_fail: false,
            is_running: Arc::new(Mutex::new(false)),
        }
    }

    pub fn with_failure() -> Self {
        Self {
            should_fail: true,
            is_running: Arc::new(Mutex::new(false)),
        }
    }

    pub async fn is_running(&self) -> bool {
        *self.is_running.lock().await
    }
}

#[async_trait]
impl Runtime for MockRuntime {
    async fn run(&self, _config: &Config) -> Result<()> {
        if self.should_fail {
            return Err(anyhow!("モックエラー: コンテナの実行に失敗しました"));
        }
        
        // 実行状態を設定
        let mut is_running = self.is_running.lock().await;
        *is_running = true;
        
        // 実行を模擬するために待機
        tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
        Ok(())
    }

    fn box_clone(&self) -> Box<dyn Runtime> {
        Box::new(Self {
            should_fail: self.should_fail,
            is_running: self.is_running.clone(),
        })
    }
} 