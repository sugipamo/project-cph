use serde::Deserialize;
use std::collections::HashMap;
use std::path::Path;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AliasError {
    #[error("Failed to read aliases file: {0}")]
    IoError(#[from] std::io::Error),
    #[error("Failed to parse aliases file: {0}")]
    YamlError(#[from] serde_yaml::Error),
}

pub type Result<T> = std::result::Result<T, AliasError>;

#[derive(Debug, Clone, Deserialize)]
pub struct AliasConfig {
    pub languages: HashMap<String, Vec<String>>,
    pub commands: HashMap<String, Vec<String>>,
    pub sites: HashMap<String, Vec<String>>,
}

impl AliasConfig {
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self> {
        let config_str = std::fs::read_to_string(path)?;
        let config: AliasConfig = serde_yaml::from_str(&config_str)?;
        Ok(config)
    }

    pub fn resolve_language(&self, input: &str) -> Option<String> {
        let input_lower = input.to_lowercase();
        for (canonical, aliases) in &self.languages {
            if canonical.to_lowercase() == input_lower {
                return Some(canonical.clone());
            }
            if aliases.iter().any(|alias| alias.to_lowercase() == input_lower) {
                return Some(canonical.clone());
            }
        }
        None
    }

    pub fn resolve_command(&self, input: &str) -> Option<String> {
        let input_lower = input.to_lowercase();
        for (canonical, aliases) in &self.commands {
            if canonical.to_lowercase() == input_lower {
                return Some(canonical.clone());
            }
            if aliases.iter().any(|alias| alias.to_lowercase() == input_lower) {
                return Some(canonical.clone());
            }
        }
        None
    }

    pub fn resolve_site(&self, input: &str) -> Option<String> {
        let input_lower = input.to_lowercase();
        for (canonical, aliases) in &self.sites {
            if canonical.to_lowercase() == input_lower {
                return Some(canonical.clone());
            }
            if aliases.iter().any(|alias| alias.to_lowercase() == input_lower) {
                return Some(canonical.clone());
            }
        }
        None
    }
} 