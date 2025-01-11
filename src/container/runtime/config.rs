use std::path::PathBuf;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Config {
    pub id: String,
    pub image: String,
    pub working_dir: PathBuf,
    pub args: Vec<String>,
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
        Self {
            memory_mb: 512,
            cpu_count: 1,
            timeout_sec: 30,
        }
    }
} 