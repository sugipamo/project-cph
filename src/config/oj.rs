use serde::{Serialize, Deserialize};
use crate::error::Result;
use crate::config::get_config_paths;

#[derive(Debug, Serialize, Deserialize)]
pub struct OJConfig {
    pub submit: SubmitConfig,
    pub test: TestConfig,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SubmitConfig {
    pub wait: u32,
    pub auto_yes: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TestConfig {
    pub directory: String,
}

impl OJConfig {
    pub fn load() -> Result<Self> {
        let config_path = get_config_paths().oj;
        if !config_path.exists() {
            return Err(format!("OJ config file not found: {}", config_path.display()).into());
        }

        let content = std::fs::read_to_string(&config_path)
            .map_err(|e| format!("Failed to read config file {}: {}", config_path.display(), e))?;
        
        let config: OJConfig = serde_yaml::from_str(&content)
            .map_err(|e| format!("Failed to parse config file {}: {}", config_path.display(), e))?;
            
        Ok(config)
    }
} 