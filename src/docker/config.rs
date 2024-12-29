use std::path::Path;
use std::collections::HashMap;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerConfig {
    pub languages: Languages,
    pub timeout_seconds: u64,
    pub memory_limit_mb: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Languages {
    pub languages: HashMap<String, LanguageConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageConfig {
    pub image: String,
    pub compile: Option<Vec<String>>,
    pub run: Vec<String>,
}

impl LanguageConfig {
    pub fn get_workspace_dir(language: &str) -> String {
        format!("/compile/{}", language)
    }
}

impl RunnerConfig {
    pub fn load<P: AsRef<Path>>(path: P) -> std::io::Result<Self> {
        println!("ランナー設定を読み込んでいます: {:?}", path.as_ref());
        let content = std::fs::read_to_string(path)?;
        serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
    }

    pub fn get_language_config(&self, language: &str) -> Option<&LanguageConfig> {
        // 完全一致を試す
        if let Some(config) = self.languages.languages.get(language) {
            return Some(config);
        }

        // エイリアスを試す
        let language = language.to_lowercase();
        match language.as_str() {
            "py" => self.languages.languages.get("python"),
            "rs" => self.languages.languages.get("rust"),
            _ => None,
        }
    }

    pub fn list_languages(&self) -> Vec<String> {
        self.languages.languages.keys().cloned().collect()
    }
} 