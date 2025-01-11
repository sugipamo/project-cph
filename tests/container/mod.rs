pub mod runtime;
pub mod communication;
pub mod io;

#[cfg(test)]
mod tests {
    use cph::container::{
        runtime::Container,
        runtime::config::Config,
        communication::Network,
        io::Buffer,
    };
    use std::path::PathBuf;
    use anyhow::Result;

    #[allow(dead_code)]
    async fn setup_test_container() -> Result<(Container, Config)> {
        let config = Config::new(
            "test-container".to_string(),
            "rust:latest".to_string(),
            PathBuf::from("/workspace"),
            vec!["sleep".to_string(), "1".to_string()],
        );
        let network = std::sync::Arc::new(Network::new());
        let buffer = std::sync::Arc::new(Buffer::new());
        let container = Container::new(config.clone(), network, buffer).await?;
        Ok((container, config))
    }
} 