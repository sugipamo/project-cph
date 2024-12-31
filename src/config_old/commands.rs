use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandConfig {
    pub commands: HashMap<String, Vec<String>>,
}

impl CommandConfig {
    pub fn load(config_path: PathBuf) -> crate::error::Result<Self> {
        if !config_path.exists() {
            return Ok(Self::default());
        }

        let content = std::fs::read_to_string(config_path)?;
        let config = serde_yaml::from_str(&content)?;
        Ok(config)
    }

    pub fn resolve_command(&self, input: &str) -> Option<String> {
        // 完全一致の場合はそのまま返す
        if self.commands.contains_key(input) {
            return Some(input.to_string());
        }

        // エイリアスを探索
        for (key, aliases) in &self.commands {
            if aliases.iter().any(|alias| alias == input) {
                return Some(key.clone());
            }
        }
        None
    }
}

impl Default for CommandConfig {
    fn default() -> Self {
        let mut commands = HashMap::new();
        commands.insert("test".to_string(), vec!["t".to_string(), "check".to_string()]);
        commands.insert("open".to_string(), vec!["o".to_string(), "show".to_string()]);
        commands.insert("submit".to_string(), vec!["s".to_string(), "sub".to_string()]);
        commands.insert("init".to_string(), vec!["i".to_string(), "create".to_string()]);
        commands.insert("language".to_string(), vec!["l".to_string(), "lang".to_string()]);
        commands.insert("login".to_string(), vec!["auth".to_string()]);

        Self { commands }
    }
} 