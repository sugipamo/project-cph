use cph::container::runtime::orchestrator::ParallelExecutor;
use cph::container::runtime::config::Config;
use cph::container::runtime::mock::TestRuntime;
use std::sync::Arc;
use anyhow::Result;
use std::path::PathBuf;

#[tokio::test]
async fn test_container_creation() -> Result<()> {
    let runtime = Arc::new(TestRuntime::new());
    let executor = ParallelExecutor::with_runtime(runtime)?;
    
    let configs = vec![
        Config::new(
            "test-python",
            "python:3.9",
            PathBuf::from("/workspace/test"),
            vec!["python".to_string(), "test.py".to_string()],
            None,
        ),
        Config::new(
            "test-rust",
            "rust:1.70",
            PathBuf::from("/workspace/src"),
            vec!["cargo".to_string(), "run".to_string()],
            None,
        ),
    ];

    executor.execute(configs).await?;
    executor.cleanup().await?;

    Ok(())
}

#[tokio::test]
async fn test_error_handling() -> Result<()> {
    let runtime = Arc::new(TestRuntime::with_failure());
    let executor = ParallelExecutor::with_runtime(runtime)?;
    
    let configs = vec![
        Config::new(
            "test-error",
            "invalid-image",
            PathBuf::from("/workspace/test"),
            vec!["invalid".to_string(), "command".to_string()],
            None,
        ),
    ];

    let result = executor.execute(configs).await;
    assert!(result.is_err());

    Ok(())
} 