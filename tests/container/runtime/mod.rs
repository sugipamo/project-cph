use anyhow::Result;
use cph::container::{
    runtime::{
        Builder,
        mock::MockRuntime,
    },
    State,
};
use std::sync::Arc;

#[tokio::test]
async fn test_container_lifecycle() -> Result<()> {
    let runtime = Arc::new(MockRuntime::new());
    let container = Builder::new()
        .with_id("test-container")
        .with_image("test-image")
        .with_runtime(runtime)
        .build();

    assert_eq!(container.status().await, State::Created);
    
    let handle = tokio::spawn({
        let container = container.clone();
        async move {
            container.run().await
        }
    });

    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    assert_eq!(container.status().await, State::Running);
    
    container.cancel().await?;
    assert_eq!(container.status().await, State::Completed);
    
    handle.abort();
    Ok(())
}

#[tokio::test]
async fn test_error_handling() -> Result<()> {
    let runtime = Arc::new(MockRuntime::with_failure());
    
    let container = Builder::new()
        .with_id("test-container")
        .with_image("test-image")
        .with_runtime(runtime)
        .build();

    let result = container.run().await;
    assert!(result.is_err());

    match container.status().await {
        State::Failed(_) => (),
        state => panic!("Expected Failed state, got {:?}", state),
    }
    
    Ok(())
}

#[tokio::test]
async fn test_python_execution() -> Result<()> {
    let runtime = Arc::new(MockRuntime::new());
    
    let container = Builder::new()
        .with_id("test-python")
        .with_image("python:3.9")
        .with_args(vec!["python".to_string(), "test.py".to_string()])
        .with_working_dir("/workspace/test")
        .with_runtime(runtime)
        .build();

    assert_eq!(container.status().await, State::Created);
    
    let handle = tokio::spawn({
        let container = container.clone();
        async move {
            container.run().await
        }
    });

    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    assert_eq!(container.status().await, State::Running);
    
    container.cancel().await?;
    assert_eq!(container.status().await, State::Completed);
    
    handle.abort();
    Ok(())
}

#[tokio::test]
async fn test_rust_execution() -> Result<()> {
    let runtime = Arc::new(MockRuntime::new());
    
    let container = Builder::new()
        .with_id("test-rust")
        .with_image("rust:1.70")
        .with_args(vec!["cargo".to_string(), "run".to_string()])
        .with_working_dir("/workspace/src")
        .with_runtime(runtime)
        .build();

    assert_eq!(container.status().await, State::Created);
    
    let handle = tokio::spawn({
        let container = container.clone();
        async move {
            container.run().await
        }
    });

    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    assert_eq!(container.status().await, State::Running);
    
    container.cancel().await?;
    assert_eq!(container.status().await, State::Completed);
    
    handle.abort();
    Ok(())
} 