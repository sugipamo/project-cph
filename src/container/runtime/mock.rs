use super::Runtime;
use super::config::Config;
use super::container::ContainerState;
use anyhow::Result;
use async_trait::async_trait;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::Duration;

#[derive(Clone)]
pub struct MockRuntime {
    should_fail: bool,
    state: Arc<Mutex<ContainerState>>,
}

impl MockRuntime {
    pub fn new() -> Self {
        println!("MockRuntime: 新規作成");
        Self {
            should_fail: false,
            state: Arc::new(Mutex::new(ContainerState::Created)),
        }
    }

    pub fn with_failure() -> Self {
        println!("MockRuntime: 失敗モードで作成");
        Self {
            should_fail: true,
            state: Arc::new(Mutex::new(ContainerState::Created)),
        }
    }

    pub async fn status(&self) -> ContainerState {
        let state = self.state.lock().await.clone();
        println!("MockRuntime: 状態取得 = {state:?}");
        state
    }
}

#[async_trait]
impl Runtime for MockRuntime {
    async fn run(&self, _config: &Config) -> Result<()> {
        if self.should_fail {
            return Err(anyhow::anyhow!("モックランタイムの実行に失敗"));
        }

        {
            *self.state.lock().await = ContainerState::Running;
            println!("MockRuntime: 状態を Running に変更");
        }

        tokio::time::sleep(Duration::from_millis(100)).await;

        {
            *self.state.lock().await = ContainerState::Completed;
            println!("MockRuntime: 状態を Completed に変更");
        }

        Ok(())
    }

    fn box_clone(&self) -> Box<dyn Runtime> {
        Box::new(self.clone())
    }
} 