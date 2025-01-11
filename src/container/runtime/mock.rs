use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::Duration;
use super::container::State;
use super::Runtime;
use super::config::Config;
use async_trait::async_trait;
use anyhow::Result;

#[derive(Clone)]
pub struct MockRuntime {
    should_fail: bool,
    state: Arc<Mutex<State>>,
}

impl MockRuntime {
    #[must_use]
    pub fn new() -> Self {
        println!("MockRuntime: 新規作成");
        Self {
            should_fail: false,
            state: Arc::new(Mutex::new(State::Created)),
        }
    }

    #[must_use]
    pub fn with_failure() -> Self {
        Self {
            should_fail: true,
            state: Arc::new(Mutex::new(State::Created)),
        }
    }

    pub async fn status(&self) -> State {
        self.state.lock().await.clone()
    }
}

#[async_trait]
impl Runtime for MockRuntime {
    async fn run(&self, _config: &Config) -> Result<()> {
        println!("MockRuntime: 実行開始");
        {
            let mut state = self.state.lock().await;
            *state = State::Running;
        }

        tokio::time::sleep(Duration::from_millis(100)).await;

        if self.should_fail {
            return Err(anyhow::anyhow!("モックエラー"));
        }

        {
            let mut state = self.state.lock().await;
            *state = State::Completed;
        }
        Ok(())
    }

    fn box_clone(&self) -> Box<dyn Runtime> {
        Box::new(self.clone())
    }
} 