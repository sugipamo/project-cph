use std::path::{Path, PathBuf};
use serde::{Serialize, Deserialize};
use crate::cli::Site;
use crate::Language;

pub mod aliases;

#[derive(Debug, Serialize, Deserialize)]
pub struct Config {
    pub contest_id: String,
    pub language: Language,
    pub site: Site,
}

impl Config {
    pub fn load<P: AsRef<Path>>(workspace_path: P) -> std::io::Result<Self> {
        let config_path = workspace_path.as_ref().join("contests.yaml");
        let content = std::fs::read_to_string(config_path)?;
        Ok(serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?)
    }
}

pub fn get_config_paths() -> ConfigPaths {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    let config_dir = home.join(".config").join("cph");
    
    ConfigPaths {
        aliases: config_dir.join("aliases.yaml"),
    }
}

pub struct ConfigPaths {
    pub aliases: PathBuf,
} 