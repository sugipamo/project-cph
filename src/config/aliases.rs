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

    /// 複数の引数を文脈を考慮して解決します
    pub fn resolve_args(&self, args: Vec<String>) -> Option<Vec<String>> {
        if args.len() < 2 {
            return Some(args);
        }

        let mut result = vec![args[0].clone()];
        let mut i = 1;
        
        // コマンドの文脈を追跡
        let mut context = CommandContext::new();
        
        while i < args.len() {
            let current_arg = &args[i];
            
            // 文脈に基づいて解決を試みる
            if let Some(resolved) = self.resolve_with_context(current_arg, &context) {
                result.push(resolved);
                context.update(&result);
            } else {
                result.push(current_arg.clone());
                context.update(&result);
            }
            i += 1;
        }

        Some(result)
    }

    /// 文脈を考慮してエイリアスを解決します
    fn resolve_with_context(&self, input: &str, context: &CommandContext) -> Option<String> {
        match context.current_position() {
            // 最初の引数（サイトまたはグローバルコマンド）
            CommandPosition::First => {
                self.resolve_site(input)
                    .or_else(|| self.resolve_command(input))
            },
            // サイト指定後のコマンド
            CommandPosition::AfterSite => {
                self.resolve_command(input)
            },
            // コマンド後の言語指定
            CommandPosition::AfterCommand => {
                if context.expects_language() {
                    self.resolve_language(input)
                } else {
                    None
                }
            },
            // その他の位置（問題ID等）
            CommandPosition::Other => None,
        }
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

/// コマンドの文脈を追跡するための補助構造体
#[derive(Debug)]
struct CommandContext {
    position: CommandPosition,
    command_type: Option<String>,
}

#[derive(Debug)]
enum CommandPosition {
    First,
    AfterSite,
    AfterCommand,
    Other,
}

impl CommandContext {
    fn new() -> Self {
        Self {
            position: CommandPosition::First,
            command_type: None,
        }
    }

    fn current_position(&self) -> &CommandPosition {
        &self.position
    }

    fn expects_language(&self) -> bool {
        matches!(self.command_type.as_deref(), Some("language"))
    }

    fn update(&mut self, args: &[String]) {
        match args.len() {
            2 => self.position = CommandPosition::AfterSite,
            3 => {
                self.position = CommandPosition::AfterCommand;
                self.command_type = Some(args[2].clone());
            },
            _ => self.position = CommandPosition::Other,
        }
    }
} 