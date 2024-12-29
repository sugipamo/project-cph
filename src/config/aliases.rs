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

#[derive(Debug, Clone, Deserialize)]
pub struct AliasConfig {
    pub languages: HashMap<String, Vec<String>>,
    pub commands: HashMap<String, Vec<String>>,
    pub sites: HashMap<String, Vec<String>>,
}

impl AliasConfig {
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self> {
        let config_str = std::fs::read_to_string(path)?;
        let config: AliasConfig = serde_yaml::from_str(&config_str)?;
        Ok(config)
    }

    pub fn resolve_language(&self, input: &str) -> Option<String> {
        let input_lower = input.to_lowercase();
        for (canonical, aliases) in &self.languages {
            if canonical.to_lowercase() == input_lower {
                return Some(canonical.clone());
            }
            if aliases.iter().any(|alias| alias.to_lowercase() == input_lower) {
                return Some(canonical.clone());
            }
        }
        None
    }

    pub fn resolve_command(&self, input: &str) -> Option<String> {
        let input_lower = input.to_lowercase();
        for (canonical, aliases) in &self.commands {
            if canonical.to_lowercase() == input_lower {
                return Some(canonical.clone());
            }
            if aliases.iter().any(|alias| alias.to_lowercase() == input_lower) {
                return Some(canonical.clone());
            }
        }
        None
    }

    /// コマンドとその引数を解決します
    /// 
    /// # Arguments
    /// * `cmd` - 解決するコマンドまたはエイリアス
    /// * `args` - コマンドの引数
    /// 
    /// # Returns
    /// * `Some((String, Vec<String>))` - 解決されたコマンドと引数のタプル
    /// * `None` - コマンドが見つからない場合
    pub fn resolve_command_with_args(&self, cmd: &str, args: Vec<String>) -> Option<(String, Vec<String>)> {
        self.resolve_command(cmd)
            .map(|resolved_cmd| (resolved_cmd, args))
    }

    /// サブコマンドの引数を含めて解決します
    /// 
    /// # Arguments
    /// * `args` - コマンドライン引数（最初の引数はプログラム名を想定）
    /// 
    /// # Returns
    /// * `Some(Vec<String>)` - 解決された引数のベクター
    /// * `None` - コマンドが見つからない場合
    pub fn resolve_args(&self, args: Vec<String>) -> Option<Vec<String>> {
        if args.len() < 2 {
            return Some(args);
        }

        let mut result = vec![args[0].clone()];
        let mut i = 1;
        
        while i < args.len() {
            if let Some(resolved) = self.resolve_command(&args[i]) {
                result.push(resolved);
            } else {
                result.push(args[i].clone());
            }
            i += 1;
        }

        Some(result)
    }

    pub fn resolve_site(&self, input: &str) -> Option<String> {
        let input_lower = input.to_lowercase();
        for (canonical, aliases) in &self.sites {
            if canonical.to_lowercase() == input_lower {
                return Some(canonical.clone());
            }
            if aliases.iter().any(|alias| alias.to_lowercase() == input_lower) {
                return Some(canonical.clone());
            }
        }
        None
    }
} 