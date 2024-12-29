pub mod traits;
pub mod resolvers;
pub mod config;

use std::collections::HashMap;
use traits::{AliasResolver, Result};

/// エイリアス解決を管理するマネージャー
pub struct AliasManager {
    resolvers: HashMap<String, Box<dyn AliasResolver>>,
}

impl AliasManager {
    pub fn new() -> Self {
        Self {
            resolvers: HashMap::new(),
        }
    }

    /// リゾルバーを追加
    pub fn add_resolver(&mut self, resolver: Box<dyn AliasResolver>) {
        self.resolvers.insert(resolver.category().to_string(), resolver);
    }

    /// エイリアスを解決
    pub fn resolve(&self, category: &str, input: &str) -> Result<String> {
        let resolver = self.resolvers.get(category)
            .ok_or_else(|| format!("カテゴリ '{}' のリゾルバーが見つかりません", category))?;
        
        let resolved = resolver.resolve(input)?;
        resolver.validate(&resolved)?;
        
        Ok(resolved)
    }
}

impl Default for AliasManager {
    fn default() -> Self {
        Self::new()
    }
}
