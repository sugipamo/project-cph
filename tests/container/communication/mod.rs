use std::sync::Arc;
use anyhow::{Result, anyhow};
use cph::container::communication::{
    transport::Network,
    protocol::Message,
};

#[tokio::test]
async fn test_message_sending() -> Result<()> {
    let network = Arc::new(Network::new());
    
    let message = Message::normal(
        "テストメッセージ",
        "sender",
        "receiver",
    );
    
    network.send("sender", "receiver", message.clone()).await?;
    
    let received = network.receive("receiver").await.ok_or_else(|| anyhow!("メッセージが受信できませんでした"))?;
    assert_eq!(received, message);
    
    Ok(())
}

#[tokio::test]
async fn test_message_broadcasting() -> Result<()> {
    let network = Arc::new(Network::new());
    
    // 受信者のバッファを事前に作成
    network.send("sender", "receiver1", Message::normal("init", "sender", "receiver1")).await?;
    network.send("sender", "receiver2", Message::normal("init", "sender", "receiver2")).await?;
    
    // 初期化メッセージを消費
    let _ = network.receive("receiver1").await;
    let _ = network.receive("receiver2").await;
    
    let message = Message::system(
        "ブロードキャストメッセージ",
        "sender",
        "all",
    );
    
    network.broadcast("sender", message.clone()).await?;
    
    let received1 = network.receive("receiver1").await.ok_or_else(|| anyhow!("メッセージが受信できませんでした"))?;
    let received2 = network.receive("receiver2").await.ok_or_else(|| anyhow!("メッセージが受信できませんでした"))?;
    
    assert_eq!(received1, message);
    assert_eq!(received2, message);
    
    Ok(())
} 