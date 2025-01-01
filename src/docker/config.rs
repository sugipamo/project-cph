use std::path::Path;
use serde::{Serialize, Deserialize};
use crate::config::{Config, ConfigError};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DockerConfig {
    pub timeout_seconds: u64,
    pub memory_limit_mb: u64,
    pub mount_point: String,
}

impl DockerConfig {
    pub fn new(timeout_seconds: u64, memory_limit_mb: u64, mount_point: String) -> Self {
        Self {
            timeout_seconds,
            memory_limit_mb,
            mount_point,
        }
    }

    pub fn default() -> Result<Self, ConfigError> {
        let config = Config::load()?;

        let timeout_seconds = config.get::<u64>("system.docker.timeout_seconds")
            .map_err(|e| ConfigError::RequiredValueError(
                format!("設定の読み込みに失敗しました: {}", e)
            ))?;

        let memory_limit_mb = config.get::<u64>("system.docker.memory_limit_mb")
            .map_err(|e| ConfigError::RequiredValueError(
                format!("設定の読み込みに失敗しました: {}", e)
            ))?;

        let mount_point = config.get::<String>("system.docker.mount_point")
            .map_err(|e| ConfigError::RequiredValueError(
                format!("設定の読み込みに失敗しました: {}", e)
            ))?;

        Ok(Self::new(timeout_seconds, memory_limit_mb, mount_point))
    }

    pub fn from_yaml<P: AsRef<Path>>(path: P) -> Result<Self, ConfigError> {
        let content = std::fs::read_to_string(path)
            .map_err(ConfigError::IoError)?;
        serde_yaml::from_str(&content)
            .map_err(|e| ConfigError::ParseError(e))
    }
} 