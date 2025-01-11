use cph::container::orchestrator::ContainerOrchestrator;
use cph::container::communication::protocol::{Message, MessageKind};
use cph::container::runtime::mock::MockRuntime;
use cph::container::runtime::builder::ContainerBuilder;
use std::sync::Arc;
use anyhow::Result;

#[tokio::test]
async fn test_multi_container_orchestration() -> Result<()> {
    let runtime = Arc::new(MockRuntime::new());
    let orchestrator = ContainerOrchestrator::new();
    
    let builder = ContainerBuilder::new().with_runtime(runtime.clone());
    orchestrator.add_container_with_builder(builder, "python", "test/script1.py", vec!["arg1".to_string()]).await?;
    orchestrator.add_container_with_builder(builder, "python", "test/script2.py", vec!["arg2".to_string()]).await?;
    orchestrator.add_container_with_builder(builder, "python", "test/script3.py", vec!["arg3".to_string()]).await?;

    orchestrator.link("script1", "script2").await?;
    orchestrator.run_all().await?;
    orchestrator.wait_all().await?;

    let status = orchestrator.get_status_summary().await;
    assert_eq!(status.total_containers, 3);
    assert_eq!(status.running_containers, 3);
    assert_eq!(status.total_links, 1);

    Ok(())
}

#[tokio::test]
async fn test_message_priority_and_routing() -> Result<()> {
    let runtime = Arc::new(MockRuntime::new());
    let orchestrator = ContainerOrchestrator::new();
    
    let builder = ContainerBuilder::new().with_runtime(runtime.clone());
    orchestrator.add_container_with_builder(builder, "python", "test/sender.py", vec![]).await?;
    orchestrator.add_container_with_builder(builder, "python", "test/receiver.py", vec![]).await?;

    orchestrator.link("sender", "receiver").await?;
    orchestrator.run_all().await?;

    orchestrator.send_message(Message::normal("通常メッセージ", "sender", "receiver")).await?;
    orchestrator.send_message(Message::system("システムメッセージ", "sender", "receiver")).await?;
    orchestrator.send_message(Message::error("エラーメッセージ", "sender", "receiver")).await?;

    let status = orchestrator.get_status_summary().await;
    assert_eq!(status.total_messages, 3);
    assert_eq!(status.message_counts.get(&MessageKind::Normal).unwrap(), &1);
    assert_eq!(status.message_counts.get(&MessageKind::System).unwrap(), &1);
    assert_eq!(status.message_counts.get(&MessageKind::Error).unwrap(), &1);

    Ok(())
}

#[tokio::test]
async fn test_network_topology_changes() -> Result<()> {
    let runtime = Arc::new(MockRuntime::new());
    let orchestrator = ContainerOrchestrator::new();
    
    let builder = ContainerBuilder::new().with_runtime(runtime.clone());
    orchestrator.add_container_with_builder(builder, "python", "test/node1.py", vec![]).await?;
    orchestrator.add_container_with_builder(builder, "python", "test/node2.py", vec![]).await?;
    orchestrator.add_container_with_builder(builder, "python", "test/node3.py", vec![]).await?;

    orchestrator.link("node1", "node2").await?;
    orchestrator.link("node2", "node3").await?;
    orchestrator.link("node3", "node1").await?;

    let isolated = orchestrator.get_isolated_containers().await;
    assert!(isolated.is_empty(), "孤立したノードが存在します");

    Ok(())
} 