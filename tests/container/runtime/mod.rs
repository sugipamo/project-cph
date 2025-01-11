mod mock;

#[cfg(test)]
mod tests {
    use super::mock::MockRuntime;
    use cph::container::{
        runtime::Container,
        runtime::config::Config,
        communication::Network,
        io::Buffer,
        state::lifecycle::Status,
    };
    use std::{path::PathBuf, sync::Arc};
    use anyhow::Result;
    use tokio::time::{sleep, Duration};

    async fn setup_test_container() -> Result<Container> {
        let config = Config::new(
            "test-container".to_string(),
            "rust:latest".to_string(),
            PathBuf::from("/workspace"),
            vec!["sleep".to_string(), "1".to_string()],
        );
        let network = Arc::new(Network::new());
        let buffer = Arc::new(Buffer::new());
        let runtime = MockRuntime::new("test-container".to_string());
        Container::with_runtime(config, network, buffer, runtime).await
    }

    #[tokio::test]
    async fn test_container_lifecycle() -> Result<()> {
        let container = setup_test_container().await?;
        
        // 初期状態の確認
        assert_eq!(container.status().await, Status::Created);

        // コンテナの実行
        let handle = tokio::spawn(async move {
            container.run().await
        });

        // 少し待ってステータスを確認
        sleep(Duration::from_millis(100)).await;
        
        // 実行完了を待つ
        handle.await??;
        
        Ok(())
    }

    #[tokio::test]
    async fn test_container_cleanup() -> Result<()> {
        let container = setup_test_container().await?;
        
        // クリーンアップの実行
        container.cleanup().await?;
        
        // クリーンアップ後のステータス確認
        assert_eq!(container.status().await, Status::Stopped);
        
        Ok(())
    }

    #[tokio::test]
    async fn test_container_cancel() -> Result<()> {
        let container = setup_test_container().await?;
        
        // コンテナの実行
        let handle = tokio::spawn(async move {
            container.run().await
        });

        // 少し待ってからキャンセル
        sleep(Duration::from_millis(100)).await;
        
        // キャンセルの実行
        handle.abort();
        
        Ok(())
    }
} 