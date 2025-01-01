use std::path::Path;
use serde::{Serialize, Deserialize};
use crate::config::Config;

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

    pub fn default() -> std::io::Result<Self> {
        let config = Config::builder()
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;

        let timeout_seconds = config.get::<u64>("system.docker.timeout_seconds")
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;

        let memory_limit_mb = config.get::<u64>("system.docker.memory_limit_mb")
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;

        let mount_point = config.get::<String>("system.docker.mount_point")
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;

        Ok(Self {
            timeout_seconds,
            memory_limit_mb,
            mount_point,
        })
    }

    pub fn from_yaml<P: AsRef<Path>>(path: P) -> std::io::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
    }
} 