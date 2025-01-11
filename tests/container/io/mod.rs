#[cfg(test)]
mod tests {
    use cph::container::io::Buffer;
    use bytes::Bytes;
    use anyhow::Result;

    #[tokio::test]
    async fn test_buffer_append() -> Result<()> {
        let buffer = Buffer::with_max_size(1024);
        let container_id = "test-container";
        let data = Bytes::from("test data");
        
        // データの追加
        buffer.append(container_id, data.clone()).await?;
        
        // 追加したデータの確認
        let output = buffer.get_output(container_id).await.unwrap();
        assert_eq!(output[0], data);
        
        Ok(())
    }

    #[tokio::test]
    async fn test_buffer_size_limit() -> Result<()> {
        let buffer = Buffer::with_max_size(10);
        let container_id = "test-container";
        let data = Bytes::from("test data that exceeds limit");
        
        // サイズ制限を超えるデータの追加
        let result = buffer.append(container_id, data).await;
        assert!(result.is_err());
        
        Ok(())
    }

    #[tokio::test]
    async fn test_buffer_cleanup() -> Result<()> {
        let buffer = Buffer::with_max_size(1024);
        let container_id = "test-container";
        
        // データの追加
        for i in 0..5 {
            let data = Bytes::from(format!("test data {}", i));
            buffer.append(container_id, data).await?;
        }
        
        // 古いデータのクリーンアップ
        buffer.cleanup_old_data(container_id, 2).await?;
        
        // 残りのデータ確認
        let output = buffer.get_output(container_id).await.unwrap();
        assert_eq!(output.len(), 2);
        
        Ok(())
    }

    #[tokio::test]
    async fn test_buffer_clear() -> Result<()> {
        let buffer = Buffer::with_max_size(1024);
        let container_id = "test-container";
        
        // データの追加
        buffer.append(container_id, Bytes::from("test data")).await?;
        
        // バッファのクリア
        buffer.clear(container_id).await;
        
        // クリア後のサイズ確認
        assert_eq!(buffer.get_size(container_id).await, 0);
        
        Ok(())
    }
} 