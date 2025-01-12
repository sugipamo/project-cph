use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use anyhow::Result;
use crate::config::Config as GlobalConfig;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub id: String,
    pub image: String,
    pub working_dir: PathBuf,
    pub args: Vec<String>,
}

impl Default for Config {
    fn default() -> Self {
        // グローバル設定から値を取得を試みる
        if let Ok(config) = GlobalConfig::get_default_config() {
            if let Ok(mount_point) = config.get::<String>("system.container.mount_point") {
                return Self {
                    id: String::new(),
                    image: String::new(),
                    working_dir: PathBuf::from(mount_point),
                    args: Vec::new(),
                };
            }
        }

        // フォールバック値
        Self {
            id: String::new(),
            image: String::new(),
            working_dir: PathBuf::from("/compile"),
            args: Vec::new(),
        }
    }
}

impl Config {
    pub fn new(id: impl Into<String>, image: impl Into<String>, working_dir: impl Into<PathBuf>, args: Vec<String>) -> Self {
        Self {
            id: id.into(),
            image: image.into(),
            working_dir: working_dir.into(),
            args,
        }
    }
}

#[derive(Clone, Debug)]
pub struct ResourceLimits {
    pub memory_mb: u64,
    pub cpu_count: u32,
    pub timeout_sec: u32,
}

impl Default for ResourceLimits {
    fn default() -> Self {
        // グローバル設定から値を取得
        if let Ok(config) = GlobalConfig::get_default_config() {
            if let Ok(memory) = config.get::<u64>("system.container.memory_limit_mb") {
                if let Ok(timeout) = config.get::<u32>("system.container.timeout_seconds") {
                    return Self {
                        memory_mb: memory,
                        cpu_count: 1,
                        timeout_sec: timeout,
                    };
                }
            }
        }

        // フォールバック値
        Self {
            memory_mb: 512,
            cpu_count: 1,
            timeout_sec: 30,
        }
    }
}

pub fn get_containerd_config() -> Result<(String, String)> {
    let config = GlobalConfig::get_default_config()?;
    let socket = config.get::<String>("system.container.runtime.containerd.socket")?;
    let namespace = config.get::<String>("system.container.runtime.containerd.namespace")?;
    Ok((socket, namespace))
} 