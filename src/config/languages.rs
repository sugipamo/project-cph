use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageConfig {
    pub languages: HashMap<String, LanguageInfo>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageInfo {
    pub aliases: Vec<String>,
    pub extension: String,
    pub templates: HashMap<String, String>,
    pub site_ids: HashMap<String, String>,
    pub display_name: String,
    pub clap_name: String,
}

impl LanguageConfig {
    pub fn load(config_path: PathBuf) -> std::io::Result<Self> {
        if !config_path.exists() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                format!("Language configuration file not found: {}", config_path.display())
            ));
        }

        let content = std::fs::read_to_string(config_path)?;
        let config = serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
        Ok(config)
    }

    pub fn resolve_language(&self, input: &str) -> Option<String> {
        let input = input.to_lowercase();
        
        // 完全一致の場合はそのまま返す
        if self.languages.contains_key(&input) {
            return Some(input);
        }

        // エイリアスを探索
        for (key, lang) in &self.languages {
            if lang.aliases.iter().any(|alias| alias.to_lowercase() == input) {
                return Some(key.clone());
            }
        }
        None
    }

    pub fn get_extension(&self, language: &str) -> Option<String> {
        self.languages.get(language).map(|l| l.extension.clone())
    }

    pub fn get_template(&self, language: &str, template_name: &str) -> Option<String> {
        self.languages.get(language)
            .and_then(|l| l.templates.get(template_name))
            .cloned()
    }

    pub fn get_site_id(&self, language: &str, site: &str) -> Option<String> {
        self.languages.get(language)
            .and_then(|l| l.site_ids.get(site))
            .cloned()
    }

    pub fn get_display_name(&self, language: &str) -> Option<String> {
        self.languages.get(language).map(|l| l.display_name.clone())
    }

    pub fn get_clap_name(&self, language: &str) -> Option<String> {
        self.languages.get(language).map(|l| l.clap_name.clone())
    }

    pub fn list_languages(&self) -> Vec<String> {
        self.languages.keys().cloned().collect()
    }
} 