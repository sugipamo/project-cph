use std::path::Path;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerConfig {
    pub timeout_seconds: u64,
    pub memory_limit_mb: u64,
    pub mount_point: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageConfig {
    pub image: String,
    pub compile: Option<Vec<String>>,
    pub run: Vec<String>,
    pub compile_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DockerConfig {
    pub timeout_seconds: u64,
    pub memory_limit_mb: u64,
    pub mount_point: String,
}

impl RunnerConfig {
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

impl LanguageConfig {
    pub fn from_yaml<P: AsRef<Path>>(path: P, language: &str) -> std::io::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let languages: serde_yaml::Value = serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;

        // languages.yaml から指定された言語の設定を取得
        let lang_config = languages["languages"][language]["runner"].clone();
        serde_yaml::from_value(lang_config)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
    }

    pub fn get_compile_dir(&self) -> &str {
        &self.compile_dir
    }

    pub fn needs_compilation(&self) -> bool {
        self.compile.is_some()
    }
}

impl DockerConfig {
    pub fn from_yaml<P: AsRef<Path>>(path: P) -> std::io::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
    }
} 