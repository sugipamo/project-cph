use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SiteConfig {
    pub sites: HashMap<String, Site>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Site {
    pub aliases: Vec<String>,
    pub url_pattern: String,
}

impl SiteConfig {
    pub fn load(config_path: PathBuf) -> std::io::Result<Self> {
        if !config_path.exists() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                format!("Site configuration file not found: {}", config_path.display())
            ));
        }

        let content = std::fs::read_to_string(config_path)?;
        let config = serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
        Ok(config)
    }

    pub fn resolve_site(&self, input: &str) -> Option<String> {
        let input = input.to_lowercase();
        
        // 完全一致の場合はそのまま返す
        if self.sites.contains_key(&input) {
            return Some(input);
        }

        // エイリアスを探索
        for (key, site) in &self.sites {
            if site.aliases.iter().any(|alias| alias.to_lowercase() == input) {
                return Some(key.clone());
            }
        }
        None
    }

    pub fn get_url_pattern(&self, site: &str) -> Option<String> {
        self.sites.get(site).map(|s| s.url_pattern.clone())
    }
} 