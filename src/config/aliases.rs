use serde::Deserialize;
use std::collections::HashMap;
use std::path::Path;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AliasError {
    #[error("Failed to read aliases file: {0}")]
    IoError(#[from] std::io::Error),
    #[error("Failed to parse aliases file: {0}")]
    YamlError(#[from] serde_yaml::Error),
}

pub type Result<T> = std::result::Result<T, AliasError>;

#[derive(Debug, Clone)]
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

#[derive(Debug, Clone, Deserialize)]
pub struct AliasConfig {
    pub languages: HashMap<String, Vec<String>>,
    pub commands: HashMap<String, Vec<String>>,
    pub sites: HashMap<String, Vec<String>>,
    #[serde(skip)]
    aliases: HashMap<String, AliasType>,
}

impl AliasConfig {
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self> {
        let config_str = std::fs::read_to_string(path)?;
        let mut config: AliasConfig = serde_yaml::from_str(&config_str)?;
        config.initialize_aliases();
        Ok(config)
    }

    fn initialize_aliases(&mut self) {
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

    pub fn resolve(&self, input: &str) -> Option<ResolvedAlias> {
        let input_lower = input.to_lowercase();
        self.aliases.get(&input_lower).map(|alias_type| {
            let resolved = match alias_type {
                AliasType::Site(s) => s.clone(),
                AliasType::Command(c) => c.clone(),
                AliasType::Language(l) => l.clone(),
            };
            ResolvedAlias {
                original: input.to_string(),
                resolved,
                alias_type: alias_type.clone(),
            }
        })
    }

    pub fn resolve_args(&self, args: Vec<String>) -> Option<Vec<String>> {
        if args.is_empty() {
            return Some(args);
        }

        let mut result = Vec::with_capacity(args.len());
        
        // プログラム名（最初の引数）はそのまま
        result.push(args[0].clone());

        // 残りの引数を解決
        for arg in args.iter().skip(1) {
            if let Some(resolved) = self.resolve(arg) {
                result.push(resolved.resolved);
            } else {
                result.push(arg.clone());
            }
        }

        Some(result)
    }
} 