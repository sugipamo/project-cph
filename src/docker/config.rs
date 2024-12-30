use std::path::Path;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerConfig {
    pub timeout: u64,
    pub memory_limit: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageConfig {
    pub image: String,
    pub compile: Option<Vec<String>>,
    pub run: Vec<String>,
    pub compile_dir: String,
}

impl RunnerConfig {
    pub fn new(timeout: u64, memory_limit: u64) -> Self {
        Self {
            timeout,
            memory_limit,
        }
    }

    pub fn default() -> Self {
        Self {
            timeout: 10,  // デフォルトタイムアウト: 10秒
            memory_limit: 512,  // デフォルトメモリ制限: 512MB
        }
    }
}

impl LanguageConfig {
    pub fn from_yaml<P: AsRef<Path>>(path: P, language: &str) -> std::io::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let languages: serde_yaml::Value = serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;

        // languages.yaml から指定された言語の設定を取得
        let lang_config = languages["languages"][language]["runner"].clone();
        serde_yaml::from_value(lang_config)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
    }

    pub fn get_compile_dir(&self) -> &str {
        &self.compile_dir
    }

    pub fn needs_compilation(&self) -> bool {
        self.compile.is_some()
    }
} 