use cph::config::Config;
use cph::docker::{DockerRunner, DockerError, RunnerState};
use cph::docker::fs::DockerFileManager;
use cph::docker::executor::DockerCommandExecutor;
use std::sync::Arc;
use tokio::sync::Mutex;
use tempfile::TempDir;
use std::path::PathBuf;

// テストヘルパー
struct TestContext {
    config: Config,
    temp_dir: TempDir,
}

impl TestContext {
    fn new() -> Self {
        Self {
            config: Config::load().unwrap(),
            temp_dir: TempDir::new().unwrap(),
        }
    }

    fn create_runner(&self, should_fail: bool) -> DockerRunner {
        let docker_config = cph::docker::config::DockerConfig::new(&self.config, "rust").unwrap();
        DockerRunner::new(self.config.clone(), "rust".to_string()).unwrap()
    }
}

#[tokio::test]
async fn test_runner_initialization() {
    let ctx = TestContext::new();
    let runner = ctx.create_runner(false);
    assert_eq!(runner.get_state().await, RunnerState::Ready);
}

#[tokio::test]
async fn test_successful_compilation() {
    let ctx = TestContext::new();
    let mut runner = ctx.create_runner(false);
    
    let result = runner.run_in_docker("fn main() { println!(\"test\"); }").await;
    assert!(result.is_ok());
    assert_eq!(runner.get_state().await, RunnerState::Completed);
}

#[tokio::test]
async fn test_compilation_error() {
    let ctx = TestContext::new();
    let mut runner = ctx.create_runner(true);
    
    let result = runner.run_in_docker("invalid rust code").await;
    assert!(result.is_err());
    assert_eq!(runner.get_state().await, RunnerState::Error);
}

#[tokio::test]
async fn test_cleanup() {
    let ctx = TestContext::new();
    let mut runner = ctx.create_runner(false);
    
    let result = runner.cleanup().await;
    assert!(result.is_ok());
} 