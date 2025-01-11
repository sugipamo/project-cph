use cph::container::orchestrator::ContainerOrchestrator;
use cph::container::runtime::{ContainerBuilder, MockRuntime};
use cph::container::communication::protocol::Message;
use cph::container::runtime::container::ContainerState;
use anyhow::Result;
use std::sync::Arc;

#[tokio::test]
async fn test_multi_container_orchestration() -> Result<()> {
    let orchestrator = ContainerOrchestrator::new();

    orchestrator.add_container("python", "test/script1.py", vec!["arg1".to_string()]).await?;
    orchestrator.add_container("python", "test/script2.py", vec!["arg2".to_string()]).await?;
    orchestrator.add_container("python", "test/script3.py", vec!["arg3".to_string()]).await?;

    orchestrator.link("script1", "script2").await?;
    orchestrator.link("script2", "script3").await?;

    orchestrator.run_all().await?;

    // コンテナの状態を確認
    let container1 = orchestrator.get_container("script1").await.unwrap();
    let container2 = orchestrator.get_container("script2").await.unwrap();
    let container3 = orchestrator.get_container("script3").await.unwrap();

    assert_eq!(container1.status().await, ContainerState::Running);
    assert_eq!(container2.status().await, ContainerState::Running);
    assert_eq!(container3.status().await, ContainerState::Running);

    orchestrator.wait_all().await?;
    Ok(())
}

#[tokio::test]
async fn test_message_priority_and_routing() -> Result<()> {
    let orchestrator = ContainerOrchestrator::new();

    orchestrator.add_container("python", "test/sender.py", vec![]).await?;
    orchestrator.add_container("python", "test/receiver.py", vec![]).await?;
    orchestrator.link("sender", "receiver").await?;

    // メッセージを送信
    orchestrator.send_message(Message::normal("テスト1", "sender", "receiver")).await?;
    orchestrator.send_message(Message::system("テスト2", "sender", "receiver")).await?;
    orchestrator.send_message(Message::error("テスト3", "sender", "receiver")).await?;

    // ステータスサマリーを確認
    let status = orchestrator.get_status_summary().await;
    assert_eq!(status.total_messages, 3);
    assert!(status.message_counts.len() >= 3);

    Ok(())
}

#[tokio::test]
async fn test_network_topology_changes() -> Result<()> {
    let orchestrator = ContainerOrchestrator::new();

    // 3つのノードを作成
    orchestrator.add_container("python", "test/node1.py", vec![]).await?;
    orchestrator.add_container("python", "test/node2.py", vec![]).await?;
    orchestrator.add_container("python", "test/node3.py", vec![]).await?;

    // リング状にリンク
    orchestrator.link("node1", "node2").await?;
    orchestrator.link("node2", "node3").await?;
    orchestrator.link("node3", "node1").await?;

    // 孤立したノードがないことを確認
    let isolated = orchestrator.get_isolated_containers().await;
    assert!(isolated.is_empty(), "Expected no isolated containers");

    Ok(())
} 