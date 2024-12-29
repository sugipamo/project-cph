use std::path::{Path, PathBuf};
use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use crate::config::languages::LanguageConfig as GlobalLanguageConfig;

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
    pub workspace_dir: String,
}

impl LanguageConfig {
    pub fn get_workspace_dir(&self) -> &str {
        &self.workspace_dir
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

        // 言語設定から拡張子を解決
        let lang_config = GlobalLanguageConfig::load(PathBuf::from("src/config/languages.yaml"))
            .ok()?;

        // 拡張子から言語を解決
        let resolved_language = lang_config.resolve_language(language)?;
        self.languages.languages.get(&resolved_language)
    }

    pub fn list_languages(&self) -> Vec<String> {
        self.languages.languages.keys().cloned().collect()
    }
} 