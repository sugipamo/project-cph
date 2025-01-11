use anyhow::{Result, anyhow};
use async_trait::async_trait;
use cph::container::runtime::{Runtime, Config};

#[derive(Clone)]
pub struct MockRuntime {
    should_fail: bool,
}

impl MockRuntime {
    pub fn new() -> Self {
        Self {
            should_fail: false,
        }
    }

    pub fn with_failure() -> Self {
        Self {
            should_fail: true,
        }
    }
}

#[async_trait]
impl Runtime for MockRuntime {
    async fn run(&self, _config: &Config) -> Result<()> {
        if self.should_fail {
            Err(anyhow!("モックエラー: コンテナの実行に失敗しました"))
        } else {
            Ok(())
        }
    }

    fn box_clone(&self) -> Box<dyn Runtime> {
        Box::new(self.clone())
    }
} 