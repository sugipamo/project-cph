use std::path::{Path, PathBuf};
use serde::{Serialize, Deserialize};
use crate::config::languages::{LanguageConfig as GlobalLanguageConfig, RunnerInfo};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerConfig {
    pub timeout_seconds: u64,
    pub memory_limit_mb: i64,
    pub mount_point: String,
}

impl RunnerConfig {
    pub fn load<P: AsRef<Path>>(path: P) -> std::io::Result<Self> {
        println!("ランナー設定を読み込んでいます: {:?}", path.as_ref());
        let content = std::fs::read_to_string(path)?;
        serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
    }

    pub fn get_language_config(&self, language: &str) -> Option<RunnerInfo> {
        let lang_config = GlobalLanguageConfig::load(PathBuf::from("src/config/languages.yaml"))
            .ok()?;
        
        let lang_info = lang_config.languages.get(language)?;
        Some(lang_info.runner.clone())
    }
} 