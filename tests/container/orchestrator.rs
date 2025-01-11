use cph::container::orchestrator::ContainerOrchestrator;
use cph::container::runtime::{ContainerBuilder, MockRuntime};
use cph::container::communication::protocol::Message;
use anyhow::Result;
use std::sync::Arc;

#[tokio::test]
async fn test_multi_container_orchestration() -> Result<()> {
    let runtime = Arc::new(MockRuntime::new());
    let orchestrator = ContainerOrchestrator::new();

    let container1 = ContainerBuilder::new()
        .with_id("container1")
        .with_image("test-image")
        .with_runtime(runtime.clone())
        .build()
        .await?;

    let container2 = ContainerBuilder::new()
        .with_id("container2")
        .with_image("test-image")
        .with_runtime(runtime.clone())
        .build()
        .await?;

    let container3 = ContainerBuilder::new()
        .with_id("container3")
        .with_image("test-image")
        .with_runtime(runtime)
        .build()
        .await?;

    orchestrator.add_container("python", "test/script1.py", vec!["arg1".to_string()]).await?;
    orchestrator.add_container("python", "test/script2.py", vec!["arg2".to_string()]).await?;
    orchestrator.add_container("python", "test/script3.py", vec!["arg3".to_string()]).await?;

    orchestrator.link("container1", "container2").await?;
    orchestrator.link("container2", "container3").await?;

    orchestrator.run_all().await?;
    orchestrator.wait_all().await?;

    Ok(())
}

#[tokio::test]
async fn test_message_priority_and_routing() -> Result<()> {
    let runtime = Arc::new(MockRuntime::new());
    let orchestrator = ContainerOrchestrator::new();

    orchestrator.add_container("python", "test/sender.py", vec![]).await?;
    orchestrator.add_container("python", "test/receiver.py", vec![]).await?;
    orchestrator.link("sender", "receiver").await?;

    orchestrator.send_message(Message::normal("テスト1", "sender", "receiver")).await?;
    orchestrator.send_message(Message::system("テスト2", "sender", "receiver")).await?;
    orchestrator.send_message(Message::error("テスト3", "sender", "receiver")).await?;

    Ok(())
}

#[tokio::test]
async fn test_network_topology_changes() -> Result<()> {
    let runtime = Arc::new(MockRuntime::new());
    let orchestrator = ContainerOrchestrator::new();

    orchestrator.add_container("python", "test/node1.py", vec![]).await?;
    orchestrator.add_container("python", "test/node2.py", vec![]).await?;
    orchestrator.add_container("python", "test/node3.py", vec![]).await?;

    orchestrator.link("container1", "container2").await?;
    orchestrator.link("container2", "container3").await?;
    orchestrator.link("container3", "container1").await?;

    let isolated = orchestrator.get_isolated_containers().await;
    assert!(isolated.is_empty(), "Expected no isolated containers");

    Ok(())
} 