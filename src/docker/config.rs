use std::path::{Path, PathBuf};
use serde::{Serialize, Deserialize};
use crate::alias::{self, AliasConfig};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerConfig {
    pub languages: Languages,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Languages {
    pub python: LanguageConfig,
    pub rust: LanguageConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageConfig {
    pub image: String,
    pub compile: Option<String>,
    pub run: String,
}

impl RunnerConfig {
    pub fn load<P: AsRef<Path>>(path: P) -> std::io::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        Ok(serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?)
    }

    pub fn get_language_config(&self, language: &str) -> Option<&LanguageConfig> {
        let config_paths = alias::get_config_paths();
        let aliases = AliasConfig::load(config_paths.aliases).ok()?;
        let language = aliases.resolve_language(language)?;

        match language.as_str() {
            "python" => Some(&self.languages.python),
            "rust" => Some(&self.languages.rust),
            _ => None,
        }
    }
} 