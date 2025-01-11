use cph::container::Orchestrator;
use cph::container::runtime::mock::MockRuntime;
use cph::container::runtime::Builder;
use cph::container::{Message, MessageKind};
use std::sync::Arc;
use anyhow::Result;

#[tokio::test]
async fn test_container_creation() -> Result<()> {
    let runtime = Arc::new(MockRuntime::new());
    let orchestrator = Orchestrator::new();
    
    let container = orchestrator.add_container_with_builder(
        Builder::new().with_runtime(runtime.clone()),
        "python",
        "test.py",
        vec!["python".to_string(), "test.py".to_string()]
    ).await?;

    let container2 = orchestrator.add_container_with_builder(
        Builder::new().with_runtime(runtime.clone()),
        "rust",
        "main.rs",
        vec!["cargo".to_string(), "run".to_string()]
    ).await?;

    let container3 = orchestrator.add_container_with_builder(
        Builder::new().with_runtime(runtime.clone()),
        "python",
        "test2.py",
        vec!["python".to_string(), "test2.py".to_string()]
    ).await?;

    orchestrator.link(&container.id(), &container2.id()).await?;
    orchestrator.link(&container2.id(), &container3.id()).await?;

    let isolated = orchestrator.get_isolated_containers().await;
    assert_eq!(isolated.len(), 0);

    Ok(())
}

#[tokio::test]
async fn test_container_execution() -> Result<()> {
    let runtime = Arc::new(MockRuntime::new());
    let orchestrator = Orchestrator::new();
    
    let _container = orchestrator.add_container_with_builder(
        Builder::new().with_runtime(runtime.clone()),
        "python",
        "test.py",
        vec!["python".to_string(), "test.py".to_string()]
    ).await?;

    let _container2 = orchestrator.add_container_with_builder(
        Builder::new().with_runtime(runtime.clone()),
        "rust",
        "main.rs",
        vec!["cargo".to_string(), "run".to_string()]
    ).await?;

    orchestrator.run_all().await?;
    orchestrator.wait_all().await?;

    Ok(())
}

#[tokio::test]
async fn test_message_handling() -> Result<()> {
    let runtime = Arc::new(MockRuntime::new());
    let orchestrator = Orchestrator::new();
    
    let container = orchestrator.add_container_with_builder(
        Builder::new().with_runtime(runtime.clone()),
        "python",
        "test.py",
        vec!["python".to_string(), "test.py".to_string()]
    ).await?;

    let container2 = orchestrator.add_container_with_builder(
        Builder::new().with_runtime(runtime.clone()),
        "rust",
        "main.rs",
        vec!["cargo".to_string(), "run".to_string()]
    ).await?;

    orchestrator.link(container.id(), container2.id()).await?;

    orchestrator.send_message(Message::normal("通常メッセージ", container.id(), container2.id())).await?;
    orchestrator.send_message(Message::system("システムメッセージ", container.id(), container2.id())).await?;
    orchestrator.send_message(Message::error("エラーメッセージ", container.id(), container2.id())).await?;

    let status = orchestrator.get_status_summary().await;
    
    assert_eq!(status.message_counts.get(&MessageKind::Normal).unwrap(), &1);
    assert_eq!(status.message_counts.get(&MessageKind::System).unwrap(), &1);
    assert_eq!(status.message_counts.get(&MessageKind::Error).unwrap(), &1);

    Ok(())
} 