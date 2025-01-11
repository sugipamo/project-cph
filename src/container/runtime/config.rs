use std::path::PathBuf;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContainerConfig {
    pub image: String,
    pub command: Vec<String>,
    pub working_dir: PathBuf,
    pub env_vars: Vec<String>,
    pub timeout_sec: Option<u64>,
}

impl ContainerConfig {
    pub fn new(
        image: String,
        command: Vec<String>,
        working_dir: PathBuf,
        env_vars: Vec<String>,
        timeout_sec: Option<u64>,
    ) -> Self {
        Self {
            image,
            command,
            working_dir,
            env_vars,
            timeout_sec,
        }
    }
} 