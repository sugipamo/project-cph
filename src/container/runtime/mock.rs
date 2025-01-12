use std::path::Path;
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use tokio::time::sleep;
use tokio::time::Duration;
use super::Runtime;
use super::config;

#[derive(Debug, Clone)]
pub struct TestRuntime {
    should_fail: bool,
}

impl TestRuntime {
    #[must_use]
    pub const fn new() -> Self {
        Self {
            should_fail: false,
        }
    }

    #[must_use]
    pub const fn with_failure() -> Self {
        Self {
            should_fail: true,
        }
    }
}

#[async_trait]
impl Runtime for TestRuntime {
    async fn create(
        &self,
        image: &str,
        command: &[String],
        working_dir: &Path,
        env_vars: &[String],
    ) -> Result<String> {
        if self.should_fail {
            return Err(anyhow!("モックエラー: コンテナの作成に失敗しました"));
        }
        println!("Mock: Creating container with image: {}, command: {:?}, working_dir: {:?}, env_vars: {:?}",
            image, command, working_dir, env_vars);
        Ok("mock-container-id".to_string())
    }

    async fn start(&self, container_id: &str) -> Result<()> {
        if self.should_fail {
            return Err(anyhow!("モックエラー: コンテナの起動に失敗しました"));
        }
        println!("Mock: Starting container: {}", container_id);
        Ok(())
    }

    async fn stop(&self, container_id: &str) -> Result<()> {
        if self.should_fail {
            return Err(anyhow!("モックエラー: コンテナの停止に失敗しました"));
        }
        println!("Mock: Stopping container: {}", container_id);
        Ok(())
    }

    async fn remove(&self, container_id: &str) -> Result<()> {
        if self.should_fail {
            return Err(anyhow!("モックエラー: コンテナの削除に失敗しました"));
        }
        println!("Mock: Removing container: {}", container_id);
        Ok(())
    }

    async fn run(&self, config: &config::Config) -> Result<()> {
        if self.should_fail {
            return Err(anyhow!("モックエラー: コンテナの実行に失敗しました"));
        }
        let prepared_config = config.prepare_image().await?;
        println!("Mock: Running container with config: {:?}", prepared_config);

        // 実行中の状態をシミュレート
        sleep(Duration::from_millis(200)).await;

        Ok(())
    }

    fn box_clone(&self) -> Box<dyn Runtime> {
        Box::new(self.clone())
    }
}

impl Default for TestRuntime {
    fn default() -> Self {
        Self::new()
    }
} 