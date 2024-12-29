use std::collections::{HashMap, HashSet};
use crate::alias::traits::{AliasResolver, Result};

/// 言語エイリアスを解決するリゾルバー
pub struct LanguageResolver {
    aliases: HashMap<String, Vec<String>>,
    valid_values: HashSet<String>,
}

impl LanguageResolver {
    pub fn new(aliases: HashMap<String, Vec<String>>, valid_values: HashSet<String>) -> Self {
        Self {
            aliases,
            valid_values,
        }
    }
}

impl AliasResolver for LanguageResolver {
    fn resolve(&self, input: &str) -> Result<String> {
        let input = input.to_lowercase();
        
        // 正規の値として存在する場合はそのまま返す
        if self.valid_values.contains(&input) {
            return Ok(input);
        }

        // エイリアスを探索
        for (key, aliases) in &self.aliases {
            if aliases.iter().any(|alias| alias.to_lowercase() == input) {
                return Ok(key.clone());
            }
        }

        Err(format!("無効な言語エイリアス: {}", input).into())
    }

    fn validate(&self, resolved: &str) -> Result<()> {
        if self.valid_values.contains(&resolved.to_lowercase()) {
            Ok(())
        } else {
            Err(format!("無効な言語: {}", resolved).into())
        }
    }

    fn category(&self) -> &str {
        "language"
    }
}
