use std::collections::{HashMap, HashSet};
use crate::alias::traits::{AliasResolver, Result};

/// サイトエイリアスを解決するリゾルバー
pub struct SiteResolver {
    aliases: HashMap<String, Vec<String>>,
    supported_sites: HashSet<String>,
}

impl SiteResolver {
    pub fn new(aliases: HashMap<String, Vec<String>>, supported_sites: HashSet<String>) -> Self {
        Self {
            aliases,
            supported_sites,
        }
    }
}

impl AliasResolver for SiteResolver {
    fn resolve(&self, input: &str) -> Result<String> {
        let input = input.to_lowercase();
        
        // 正規の値として存在する場合はそのまま返す
        if self.supported_sites.contains(&input) {
            return Ok(input);
        }

        // エイリアスを探索
        for (key, aliases) in &self.aliases {
            if aliases.iter().any(|alias| alias.to_lowercase() == input) {
                return Ok(key.clone());
            }
        }

        Err(format!("無効なサイトエイリアス: {}", input).into())
    }

    fn validate(&self, resolved: &str) -> Result<()> {
        if self.supported_sites.contains(&resolved.to_lowercase()) {
            Ok(())
        } else {
            Err(format!("サポートされていないサイト: {}", resolved).into())
        }
    }

    fn category(&self) -> &str {
        "site"
    }
}
