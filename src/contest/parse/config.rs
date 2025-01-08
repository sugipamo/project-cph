use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use anyhow::Result;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AliasInfo {
    pub original: String,
    pub category: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub commands: HashMap<String, HashMap<String, CommandValue>>,
    #[serde(skip)]
    alias_map: HashMap<String, AliasInfo>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum CommandValue {
    Command { aliases: Vec<String> },
    Setting { priority: i32 },
}

impl Default for Config {
    fn default() -> Self {
        Self::new()
    }
}

impl Config {
    #[must_use = "この関数は新しいConfigインスタンスを返します"]
    pub fn new() -> Self {
        Self::from_file("src/config/commands.yaml").unwrap_or_else(|_| Self::default_config())
    }

    /// ファイルからConfigを読み込みます
    /// 
    /// # Errors
    /// 
    /// - ファイルが存在しない場合
    /// - ファイルの読み込みに失敗した場合
    /// - YAMLのパースに失敗した場合
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let contents = fs::read_to_string(path)?;
        let mut config: Self = serde_yaml::from_str(&contents)?;
        config.build_alias_map();
        Ok(config)
    }

    fn default_config() -> Self {
        let mut commands = HashMap::new();
        let alias_map = HashMap::new();
        
        // デフォルトの設定
        let mut sites = HashMap::new();
        sites.insert(
            "atcoder".to_string(),
            CommandValue::Command {
                aliases: vec!["at".to_string()],
            },
        );
        commands.insert("site".to_string(), sites);

        let mut languages = HashMap::new();
        languages.insert(
            "rust".to_string(),
            CommandValue::Command {
                aliases: vec!["rs".to_string()],
            },
        );
        commands.insert("language".to_string(), languages);

        let mut config = Self { commands, alias_map };
        config.build_alias_map();
        config
    }

    fn build_alias_map(&mut self) {
        self.alias_map.clear();
        for (category, subcmds) in &self.commands {
            for (original, value) in subcmds {
                match value {
                    CommandValue::Command { aliases } => {
                        for alias in aliases {
                            if !alias.contains(char::is_whitespace) {
                                self.alias_map.insert(
                                    alias.clone(),
                                    AliasInfo {
                                        original: original.clone(),
                                        category: category.clone(),
                                    },
                                );
                            }
                        }
                    }
                    CommandValue::Setting { priority: _ } => {
                        // priorityの設定は無視
                    }
                }
            }
        }
    }

    /// トークンに対応するエイリアスを解決します
    /// 
    /// 返り値は (コマンドタイプ, 実際の値) のタプルです
    #[must_use]
    pub fn resolve_alias(&self, token: &str) -> Option<(String, String)> {
        self.alias_map.get(token).map(|info| {
            (info.category.clone(), info.original.clone())
        })
    }
}