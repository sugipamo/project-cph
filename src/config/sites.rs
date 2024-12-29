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
    pub supported_languages: Vec<String>,
}

impl SiteConfig {
    pub fn load(config_path: PathBuf) -> crate::error::Result<Self> {
        if !config_path.exists() {
            return Ok(Self::default());
        }

        let content = std::fs::read_to_string(config_path)?;
        let config = serde_yaml::from_str(&content)?;
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

    pub fn is_language_supported(&self, site: &str, language: &str) -> bool {
        self.sites.get(site)
            .map(|s| s.supported_languages.contains(&language.to_string()))
            .unwrap_or(false)
    }
}

impl Default for SiteConfig {
    fn default() -> Self {
        let mut sites = HashMap::new();
        
        // AtCoder
        let atcoder = Site {
            aliases: vec![
                "at-coder".to_string(),
                "at_coder".to_string(),
                "AtCoder".to_string(),
                "ac".to_string(),
            ],
            url_pattern: "https://atcoder.jp/contests/{contest_id}/tasks/{problem_id}".to_string(),
            supported_languages: vec![
                "python".to_string(),
                "rust".to_string(),
                "cpp".to_string(),
            ],
        };
        sites.insert("atcoder".to_string(), atcoder);

        Self { sites }
    }
} 