#[cfg(test)]
mod tests {
    use cph::container::communication::{
        Network,
        protocol::{Message, ControlMessage, StatusMessage},
    };
    use cph::container::state::lifecycle::Status;
    use anyhow::Result;

    #[tokio::test]
    async fn test_network_registration() -> Result<()> {
        let network = Network::new();
        let (tx, mut rx) = network.register("test-container").await?;
        
        // 送信テスト
        let message = Message::Control(ControlMessage::Start);
        tx.send(message.clone()).await?;
        
        // 受信確認
        let received = rx.recv().await.unwrap();
        assert!(matches!(received, Message::Control(ControlMessage::Start)));
        
        Ok(())
    }

    #[tokio::test]
    async fn test_network_send() -> Result<()> {
        let network = Network::new();
        let container_id = "test-container";
        let (_tx, mut rx) = network.register(container_id).await?;
        
        // メッセージ送信
        let message = Message::Status(StatusMessage {
            container_id: container_id.to_string(),
            status: Status::Running,
        });
        network.send("sender", container_id, message.clone()).await?;
        
        // 受信確認
        let received = rx.recv().await.unwrap();
        assert!(matches!(received, Message::Status(_)));
        
        Ok(())
    }

    #[tokio::test]
    async fn test_network_broadcast() -> Result<()> {
        let network = Network::new();
        
        // 複数のコンテナを登録
        let mut receivers = Vec::new();
        let container_ids = vec!["container1", "container2", "container3"];
        for id in &container_ids {
            let (_tx, rx) = network.register(id).await?;
            receivers.push((id.to_string(), rx));
        }
        
        // ブロードキャストメッセージ
        let message = Message::Control(ControlMessage::Stop);
        network.broadcast("container1", message.clone()).await?;
        
        // 全てのレシーバーでメッセージを確認
        for (id, mut rx) in receivers {
            if id != "container1" {  // 送信元以外のコンテナでメッセージを確認
                let received = rx.recv().await.unwrap();
                assert!(matches!(received, Message::Control(ControlMessage::Stop)));
            }
        }
        
        Ok(())
    }
} 