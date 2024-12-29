use std::collections::{HashMap, HashSet};
use std::path::Path;
use serde::{Deserialize, Serialize};
use crate::alias::{AliasManager, resolvers::{LanguageResolver, SiteResolver}};

#[derive(Debug, Serialize, Deserialize)]
pub struct ResolverConfig {
    valid_values: Vec<String>,
    aliases: HashMap<String, Vec<String>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AliasConfig {
    resolvers: HashMap<String, ResolverConfig>,
}

impl AliasConfig {
    /// 設定ファイルから読み込む
    pub fn from_file<P: AsRef<Path>>(path: P) -> std::io::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        Ok(serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?)
    }

    /// AliasManagerを構築する
    pub fn build_manager(&self) -> AliasManager {
        let mut manager = AliasManager::new();

        // 言語リゾルバーの設定
        if let Some(lang_config) = self.resolvers.get("language") {
            let valid_values: HashSet<_> = lang_config.valid_values.iter()
                .map(|s| s.to_lowercase())
                .collect();
            
            let aliases = lang_config.aliases.clone();
            manager.add_resolver(Box::new(LanguageResolver::new(aliases, valid_values)));
        }

        // サイトリゾルバーの設定
        if let Some(site_config) = self.resolvers.get("site") {
            let supported_sites: HashSet<_> = site_config.valid_values.iter()
                .map(|s| s.to_lowercase())
                .collect();
            
            let aliases = site_config.aliases.clone();
            manager.add_resolver(Box::new(SiteResolver::new(aliases, supported_sites)));
        }

        manager
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_alias_resolution() {
        let config = AliasConfig {
            resolvers: {
                let mut map = HashMap::new();
                
                // 言語の設定
                map.insert("language".to_string(), ResolverConfig {
                    valid_values: vec!["python".to_string(), "cpp".to_string()],
                    aliases: {
                        let mut aliases = HashMap::new();
                        aliases.insert("python".to_string(), vec!["py".to_string()]);
                        aliases.insert("cpp".to_string(), vec!["c++".to_string()]);
                        aliases
                    },
                });

                // サイトの設定
                map.insert("site".to_string(), ResolverConfig {
                    valid_values: vec!["atcoder".to_string()],
                    aliases: {
                        let mut aliases = HashMap::new();
                        aliases.insert("atcoder".to_string(), vec!["ac".to_string()]);
                        aliases
                    },
                });

                map
            },
        };

        let manager = config.build_manager();

        // 言語の解決をテスト
        assert_eq!(manager.resolve("language", "py").unwrap(), "python");
        assert_eq!(manager.resolve("language", "c++").unwrap(), "cpp");

        // サイトの解決をテスト
        assert_eq!(manager.resolve("site", "ac").unwrap(), "atcoder");
    }
}
