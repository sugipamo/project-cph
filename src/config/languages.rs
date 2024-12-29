use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageConfig {
    pub languages: HashMap<String, Language>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Language {
    pub aliases: Vec<String>,
    pub extension: String,
    pub templates: HashMap<String, String>,
    pub site_ids: HashMap<String, String>,
}

impl LanguageConfig {
    pub fn load(config_path: PathBuf) -> crate::error::Result<Self> {
        if !config_path.exists() {
            return Ok(Self::default());
        }

        let content = std::fs::read_to_string(config_path)?;
        let config = serde_yaml::from_str(&content)?;
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
}

impl Default for LanguageConfig {
    fn default() -> Self {
        let mut languages = HashMap::new();
        
        // Rust
        let mut rust = Language {
            aliases: vec!["Rust".to_string(), "rs".to_string()],
            extension: "rs".to_string(),
            templates: HashMap::new(),
            site_ids: HashMap::new(),
        };
        rust.templates.insert("default".to_string(), "template/main.rs".to_string());
        rust.site_ids.insert("atcoder".to_string(), "5054".to_string());
        languages.insert("rust".to_string(), rust);

        // Python
        let mut python = Language {
            aliases: vec!["Python".to_string(), "python3".to_string()],
            extension: "py".to_string(),
            templates: HashMap::new(),
            site_ids: HashMap::new(),
        };
        python.templates.insert("default".to_string(), "template/main.py".to_string());
        python.site_ids.insert("atcoder".to_string(), "4006".to_string());
        languages.insert("python".to_string(), python);

        Self { languages }
    }
} 