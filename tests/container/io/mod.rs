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

    #[tokio::test]
    async fn test_program_output_buffering() -> Result<()> {
        let buffer = Buffer::with_max_size(1024);
        let container_id = "test-program";
        
        // プログラム出力のシミュレーション
        let outputs = vec![
            "Compiling...\n",
            "Running tests...\n",
            "Test 1 passed\n",
            "Test 2 passed\n",
            "All tests passed!\n"
        ];
        
        // 出力の追加
        for output in outputs.iter() {
            buffer.append(container_id, Bytes::from(output.to_string())).await?;
        }
        
        // バッファの取得と検証
        let stored_output = buffer.get_output(container_id).await.unwrap();
        let combined_output: String = stored_output.iter()
            .map(|bytes| String::from_utf8_lossy(bytes).to_string())
            .collect();
        
        assert!(combined_output.contains("Compiling..."));
        assert!(combined_output.contains("All tests passed!"));
        
        Ok(())
    }

    #[tokio::test]
    async fn test_large_output_handling() -> Result<()> {
        let buffer = Buffer::with_max_size(100); // 小さいバッファサイズ
        let container_id = "test-large-output";
        
        // 大きな出力のシミュレーション
        let large_output = "X".repeat(200);
        
        // バッファサイズを超える出力を追加
        let result = buffer.append(container_id, Bytes::from(large_output)).await;
        assert!(result.is_err()); // バッファオーバーフローのエラーを確認
        
        Ok(())
    }
} 