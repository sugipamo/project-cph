use std::sync::Arc;
use std::path::PathBuf;
use anyhow::{Result, anyhow};
use crate::container::{
    communication::transport::Network,
    io::buffer::Buffer,
};
use super::{Container, Config, ResourceLimits};

/// コンテナのビルダー
#[derive(Default)]
#[allow(clippy::module_name_repetitions)]
pub struct ContainerBuilder {
    config: Option<Config>,
    network: Option<Arc<Network>>,
    buffer: Option<Arc<Buffer>>,
    resource_limits: Option<ResourceLimits>,
}

impl ContainerBuilder {
    /// 新しいビルダーを作成します
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// 設定を追加します
    #[must_use]
    pub fn with_config(self, config: Config) -> Self {
        Self {
            config: Some(config),
            ..self
        }
    }

    /// ネットワークを追加します
    #[must_use]
    pub fn with_network(self, network: Arc<Network>) -> Self {
        Self {
            network: Some(network),
            ..self
        }
    }

    /// バッファを追加します
    #[must_use]
    pub fn with_buffer(self, buffer: Arc<Buffer>) -> Self {
        Self {
            buffer: Some(buffer),
            ..self
        }
    }

    /// リソース制限を追加します
    #[must_use]
    pub fn with_resource_limits(self, limits: ResourceLimits) -> Self {
        Self {
            resource_limits: Some(limits),
            ..self
        }
    }

    /// 言語固有の設定でコンテナを構築します
    ///
    /// # Errors
    /// - 必要な設定が不足している場合
    pub async fn build_for_language(
        self,
        language: &str,
        source_file: &str,
        args: Vec<String>,
    ) -> Result<Container> {
        let working_dir = PathBuf::from("/workspace")
            .join(source_file)
            .parent()
            .unwrap_or(&PathBuf::from("/workspace"))
            .to_path_buf();

        let config = Config::new(
            format!("{language}-container"),
            format!("{language}:latest"),
            working_dir,
            args,
        );

        self.with_config(config).build().await
    }

    /// コンテナを構築します
    ///
    /// # Errors
    /// - 必要な設定が不足している場合
    pub async fn build(self) -> Result<Container> {
        let config = self.config.ok_or_else(|| anyhow!("設定が必要です"))?;
        let network = self.network.ok_or_else(|| anyhow!("ネットワークが必要です"))?;
        let buffer = self.buffer.ok_or_else(|| anyhow!("バッファが必要です"))?;

        let mut container = Container::new(config, network, buffer).await?;

        if let Some(limits) = &self.resource_limits {
            container.set_resource_limits(limits);
        }

        Ok(container)
    }
} 