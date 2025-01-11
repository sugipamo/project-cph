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
        println!("MockRuntime: 状態取得 = {:?}", state);
        state
    }
}

#[async_trait]
impl Runtime for MockRuntime {
    async fn run(&self, _config: &Config) -> Result<()> {
        println!("MockRuntime: run開始");
        if self.should_fail {
            println!("MockRuntime: 失敗モードのため、エラーを返します");
            *self.state.lock().await = ContainerState::Failed("Mock runtime failure".to_string());
            return Err(anyhow::anyhow!("Mock runtime failure"));
        }

        // コンテナの状態遷移をシミュレート
        {
            let mut state = self.state.lock().await;
            *state = ContainerState::Running;
            println!("MockRuntime: 状態を Running に変更");
        }

        // テストが状態を確認できるように十分な時間待機
        println!("MockRuntime: Running状態を維持（200ms）");
        tokio::time::sleep(Duration::from_millis(200)).await;

        // 正常終了
        {
            let mut state = self.state.lock().await;
            *state = ContainerState::Completed;
            println!("MockRuntime: 状態を Completed に変更");
        }

        println!("MockRuntime: run正常終了");
        Ok(())
    }

    fn box_clone(&self) -> Box<dyn Runtime> {
        Box::new(self.clone())
    }
} 