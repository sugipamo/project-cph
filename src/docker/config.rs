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
        Self::from_config(&config)
    }

    pub fn from_config(config: &Config) -> Result<Self, ConfigError> {
        let timeout_seconds = config.get::<u64>("system.docker.timeout_seconds")
            .map_err(|e| ConfigError::RequiredValueError(
                format!("タイムアウト設定の読み込みに失敗しました: {}", e)
            ))?;

        let memory_limit_mb = config.get::<u64>("system.docker.memory_limit_mb")
            .map_err(|e| ConfigError::RequiredValueError(
                format!("メモリ制限設定の読み込みに失敗しました: {}", e)
            ))?;

        let mount_point = config.get::<String>("system.docker.mount_point")
            .map_err(|e| ConfigError::RequiredValueError(
                format!("マウントポイント設定の読み込みに失敗しました: {}", e)
            ))?;

        Ok(Self::new(timeout_seconds, memory_limit_mb, mount_point))
    }

    pub fn from_yaml<P: AsRef<Path>>(path: P) -> Result<Self, ConfigError> {
        let content = std::fs::read_to_string(path)
            .map_err(ConfigError::IoError)?;
        serde_yaml::from_str(&content)
            .map_err(ConfigError::ParseError)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::ConfigBuilder;

    #[test]
    fn test_docker_config_from_config() -> Result<(), ConfigError> {
        let builder = ConfigBuilder::new()
            .add_required_value(
                "system.docker.timeout_seconds",
                "実行タイムアウト時間",
                crate::config::ConfigType::Integer
            )
            .add_required_value(
                "system.docker.memory_limit_mb",
                "メモリ制限",
                crate::config::ConfigType::Integer
            )
            .add_required_value(
                "system.docker.mount_point",
                "マウントポイント",
                crate::config::ConfigType::String
            );

        let config = Config::load()?;
        let docker_config = DockerConfig::from_config(&config)?;

        assert!(docker_config.timeout_seconds > 0);
        assert!(docker_config.memory_limit_mb > 0);
        assert!(!docker_config.mount_point.is_empty());

        Ok(())
    }
} 