pub mod runtime;
pub mod communication;
pub mod io;
pub mod orchestrator;

#[cfg(test)]
mod tests {
    use cph::container::{
        runtime::{
            Builder,
            mock::MockRuntime,
        },
        State,
    };
    use std::sync::Arc;
    use anyhow::Result;

    #[tokio::test]
    async fn test_container_creation() -> Result<()> {
        let runtime = Arc::new(MockRuntime::new());
        let container = Builder::new()
            .with_id("test-container")
            .with_image("test-image")
            .with_runtime(runtime)
            .build();

        assert_eq!(container.status().await, State::Created);
        Ok(())
    }

    #[tokio::test]
    async fn test_container_execution() -> Result<()> {
        let runtime = Arc::new(MockRuntime::new());
        let container = Builder::new()
            .with_id("test-container")
            .with_image("test-image")
            .with_runtime(runtime)
            .build();

        let handle = tokio::spawn({
            let container = container.clone();
            async move {
                container.run().await
            }
        });

        tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
        assert_eq!(container.status().await, State::Running);
        
        container.cancel().await?;
        assert_eq!(container.status().await, State::Completed);
        
        handle.abort();
        Ok(())
    }
} 