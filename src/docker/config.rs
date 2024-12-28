use serde::Deserialize;
use std::path::Path;
use crate::docker::error::{DockerError, Result};

#[derive(Debug, Clone, Deserialize)]
pub struct LanguageConfig {
    pub image_name: String,
    pub compile_cmd: Option<Vec<String>>,
    pub run_cmd: Vec<String>,
    pub file_extension: String,
    pub workspace_dir: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Languages {
    pub python: LanguageConfig,
    pub cpp: LanguageConfig,
    pub rust: LanguageConfig,
}

#[derive(Debug, Clone, Deserialize)]
pub struct RunnerConfig {
    pub timeout_seconds: u64,
    pub memory_limit_mb: i64,
    pub languages: Languages,
}

impl RunnerConfig {
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self> {
        let config_str = std::fs::read_to_string(path)?;
        let config: RunnerConfig = serde_yaml::from_str(&config_str)?;
        Ok(config)
    }

    pub fn get_language_config(&self, lang: &str) -> Option<&LanguageConfig> {
        match lang {
            "python" => Some(&self.languages.python),
            "cpp" => Some(&self.languages.cpp),
            "rust" => Some(&self.languages.rust),
            _ => None,
        }
    }

    pub fn validate_language(&self, lang: &str) -> Result<()> {
        if self.get_language_config(lang).is_none() {
            return Err(DockerError::UnsupportedLanguage(lang.to_string()));
        }
        Ok(())
    }
} 