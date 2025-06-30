use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub app_name: String,
    pub version: String,
    pub log_level: String,
    pub database_path: String,
    pub docker: DockerConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DockerConfig {
    pub enabled: bool,
    pub socket_path: Option<String>,
    pub default_image: String,
}

#[async_trait::async_trait]
pub trait ConfigProvider: Send + Sync {
    async fn load(&self, path: &Path) -> Result<AppConfig>;
    async fn save(&self, path: &Path, config: &AppConfig) -> Result<()>;
    async fn get(&self) -> Result<AppConfig>;
    async fn reload(&self) -> Result<()>;
}