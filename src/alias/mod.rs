use serde::{Serialize, Deserialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AliasError {
    #[error("エイリアス設定ファイルの読み込みに失敗しました: {0}")]
    IoError(#[from] std::io::Error),
    #[error("エイリアス設定ファイルの解析に失敗しました: {0}")]
    YamlError(#[from] serde_yaml::Error),
    #[error("エイリアスの解決に失敗しました: {0}")]
    ResolutionError(String),
}

pub type Result<T> = std::result::Result<T, AliasError>;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AliasType {
    Site(String),
    Command(String),
    Language(String),
}

#[derive(Debug, Clone)]
pub struct ResolvedAlias {
    pub original: String,
    pub resolved: String,
    pub alias_type: AliasType,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AliasConfig {
    pub languages: HashMap<String, Vec<String>>,
    pub sites: HashMap<String, Vec<String>>,
    pub commands: HashMap<String, Vec<String>>,
    pub aliases: HashMap<String, AliasType>,
}

impl AliasConfig {
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self> {
        let config_str = std::fs::read_to_string(path)?;
        let mut config: AliasConfig = serde_yaml::from_str(&config_str)?;
        config.initialize_aliases();
        Ok(config)
    }

    fn initialize_aliases(&mut self) {
        self.aliases = HashMap::new();
        
        // サイトのエイリアスを初期化
        for (site, aliases) in &self.sites {
            self.aliases.insert(site.to_lowercase(), AliasType::Site(site.clone()));
            for alias in aliases {
                self.aliases.insert(alias.to_lowercase(), AliasType::Site(site.clone()));
            }
        }

        // コマンドのエイリアスを初期化
        for (cmd, aliases) in &self.commands {
            self.aliases.insert(cmd.to_lowercase(), AliasType::Command(cmd.clone()));
            for alias in aliases {
                self.aliases.insert(alias.to_lowercase(), AliasType::Command(cmd.clone()));
            }
        }

        // 言語のエイリアスを初期化
        for (lang, aliases) in &self.languages {
            self.aliases.insert(lang.to_lowercase(), AliasType::Language(lang.clone()));
            for alias in aliases {
                self.aliases.insert(alias.to_lowercase(), AliasType::Language(lang.clone()));
            }
        }
    }

    pub fn resolve_language(&self, input: &str) -> Option<String> {
        let input = input.to_lowercase();
        
        // 正規の値として存在する場合はそのまま返す
        if self.languages.contains_key(&input) {
            return Some(input);
        }

        // エイリアスを探索
        for (key, aliases) in &self.languages {
            if aliases.iter().any(|alias| alias.to_lowercase() == input) {
                return Some(key.clone());
            }
        }
        None
    }

    pub fn resolve_site(&self, input: &str) -> Option<String> {
        let input = input.to_lowercase();
        
        // 正規の値として存在する場合はそのまま返す
        if self.sites.contains_key(&input) {
            return Some(input);
        }

        // エイリアスを探索
        for (key, aliases) in &self.sites {
            if aliases.iter().any(|alias| alias.to_lowercase() == input) {
                return Some(key.clone());
            }
        }
        None
    }
}

pub fn get_config_paths() -> ConfigPaths {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    let config_dir = home.join(".config").join("cph");
    
    ConfigPaths {
        aliases: config_dir.join("aliases.yaml"),
    }
}

pub struct ConfigPaths {
    pub aliases: PathBuf,
}
