use cphelper::container::io::buffer::OutputBuffer;
use bytes::Bytes;
use anyhow::Result;

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_output_buffer_write() -> Result<()> {
        let buffer = OutputBuffer::new();
        let container_id = "test_container";
        let test_data = Bytes::from("Hello, World!\n");
        
        buffer.append(container_id, test_data.clone()).await?;
        let output = buffer.get_output(container_id).await;
        assert!(output.is_some());
        assert_eq!(output.unwrap()[0], test_data);
        Ok(())
    }

    #[tokio::test]
    async fn test_output_buffer_clear() -> Result<()> {
        let buffer = OutputBuffer::new();
        let container_id = "test_container";
        let test_data = Bytes::from("Test Message\n");
        
        buffer.append(container_id, test_data).await?;
        buffer.clear(container_id).await;
        
        let size = buffer.get_size(container_id).await;
        assert_eq!(size, 0);
        Ok(())
    }

    #[tokio::test]
    async fn test_buffer_memory_usage() -> Result<()> {
        let buffer = OutputBuffer::new();
        let container_id = "test_container";
        let test_data = Bytes::from("Test Data");
        
        buffer.append(container_id, test_data).await?;
        let usage = buffer.get_total_memory_usage().await;
        assert!(usage > 0);
        Ok(())
    }
} 