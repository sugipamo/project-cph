use super::Runtime;
use super::config::Config;
use anyhow::Result;
use async_trait::async_trait;

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

    #[allow(dead_code)]
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
            Err(anyhow::anyhow!("Mock runtime failure"))
        } else {
            Ok(())
        }
    }

    fn box_clone(&self) -> Box<dyn Runtime> {
        Box::new(self.clone())
    }
} 