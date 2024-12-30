use std::path::Path;
use serde::{Serialize, Deserialize};

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

    pub fn default() -> Self {
        Self {
            timeout_seconds: 10,  // デフォルトタイムアウト: 10秒
            memory_limit_mb: 512,  // デフォルトメモリ制限: 512MB
            mount_point: "/compile".to_string(),  // デフォルトマウントポイント
        }
    }

    pub fn from_yaml<P: AsRef<Path>>(path: P) -> std::io::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
    }
} 