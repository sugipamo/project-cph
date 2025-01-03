use std::error::Error;
use std::collections::HashMap;
use serde_yaml::Value;
use crate::config::{Config, ConfigError};

#[derive(Debug, Clone, PartialEq)]
pub struct CommandType {
    pub name: String,
    pub aliases: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct ResolvedCommand {
    pub commands: Vec<String>,
    pub args: HashMap<String, String>,
}

#[derive(Debug)]
pub enum ParseError {
    InvalidCommand(String),
    ConfigError(ConfigError),
    InvalidArgument(String),
    MissingSection(String),
    InvalidPriority(String),
}

impl std::fmt::Display for ParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ParseError::InvalidCommand(msg) => write!(f, "無効なコマンド: {}", msg),
            ParseError::ConfigError(err) => write!(f, "設定エラー: {}", err),
            ParseError::InvalidArgument(msg) => write!(f, "無効な引数: {}", msg),
            ParseError::MissingSection(msg) => write!(f, "設定セクションが見つかりません: {}", msg),
            ParseError::InvalidPriority(msg) => write!(f, "無効な優先度設定: {}", msg),
        }
    }
}

impl Error for ParseError {}

impl From<ConfigError> for ParseError {
    fn from(err: ConfigError) -> Self {
        ParseError::ConfigError(err)
    }
}

pub struct NameResolver {
    command_aliases: HashMap<String, CommandType>,
    settings: HashMap<String, Value>,
}

impl NameResolver {
    pub fn new(config: &Config) -> Result<Self, ParseError> {
        let mut command_aliases = HashMap::new();
        let executions = config.get_raw_value("executions")
            .map_err(|_| ParseError::MissingSection("executions".to_string()))?;

        if let Value::Mapping(executions) = executions {
            for (cmd_name, cmd_config) in executions {
                if let (Value::String(name), Value::Mapping(config)) = (cmd_name, cmd_config) {
                    if let Some(Value::Sequence(aliases)) = config.get("aliases") {
                        let aliases: Vec<String> = aliases.iter()
                            .filter_map(|v| v.as_str())
                            .map(|s| s.to_lowercase())
                            .collect();
                        
                        let command_type = CommandType {
                            name: name.clone(),
                            aliases: aliases.clone(),
                        };

                        // 各エイリアスをマップに登録
                        for alias in aliases {
                            command_aliases.insert(alias, command_type.clone());
                        }
                    }
                }
            }
        }

        let settings = config.get_raw_value("settings")
            .map_err(|_| ParseError::MissingSection("settings".to_string()))?;

        if let Value::Mapping(settings) = settings {
            Ok(Self {
                command_aliases,
                settings: settings.iter()
                    .map(|(k, v)| (k.as_str().unwrap_or_default().to_string(), v.clone()))
                    .collect(),
            })
        } else {
            Err(ParseError::ConfigError(ConfigError::TypeError {
                expected: crate::config::ConfigType::StringArray,
                found: "not_mapping",
                path: "settings".to_string(),
                value: "".to_string(),
            }))
        }
    }

    pub fn resolve(&self, input: &str) -> Result<ResolvedCommand, ParseError> {
        // 空白の正規化と分割
        let tokens: Vec<&str> = input
            .split_whitespace()
            .collect();

        if tokens.is_empty() {
            return Err(ParseError::InvalidCommand("コマンドが空です".to_string()));
        }

        // コマンドの解決
        let mut commands = Vec::new();
        let mut current_pos = 0;
        let mut remaining_tokens = Vec::new();

        while current_pos < tokens.len() {
            let token = tokens[current_pos].to_lowercase();
            if let Some(command) = self.command_aliases.get(&token) {
                commands.push(command.name.clone());
                current_pos += 1;
            } else {
                // コマンドとして解決できないトークンは残りの引数として扱う
                break;
            }
        }

        if commands.is_empty() {
            return Err(ParseError::InvalidCommand("有効なコマンドが見つかりません".to_string()));
        }

        // 残りのトークンを収集
        remaining_tokens.extend(tokens[current_pos..].iter().map(|&s| s.to_string()));

        // 設定値の解決
        let mut args = HashMap::new();
        let mut unresolved_tokens = remaining_tokens.clone();

        // 優先度順に設定値を解決
        let mut priorities: Vec<(String, i32)> = Vec::new();
        for (key, value) in &self.settings {
            if let Value::Mapping(setting) = value {
                if let Some(Value::Number(priority)) = setting.get("priority") {
                    if let Some(priority) = priority.as_i64() {
                        priorities.push((key.clone(), priority as i32));
                    }
                }
            }
        }

        // 優先度の高い（数値が大きい）順にソート
        priorities.sort_by(|a, b| b.1.cmp(&a.1));

        for (setting_name, _) in priorities {
            if let Some(setting_value) = self.settings.get(&setting_name) {
                if unresolved_tokens.is_empty() {
                    break;
                }

                if let Some(resolved_value) = self.try_resolve_setting(
                    setting_value,
                    &unresolved_tokens[0],
                )? {
                    args.insert(setting_name.clone(), resolved_value);
                    unresolved_tokens.remove(0);
                }
            }
        }

        // 未解決のトークンがある場合は問題IDとして扱う
        if !unresolved_tokens.is_empty() {
            args.insert("problem_id".to_string(), unresolved_tokens.join(" "));
        }

        Ok(ResolvedCommand { commands, args })
    }

    fn try_resolve_setting(
        &self,
        setting: &Value,
        token: &str,
    ) -> Result<Option<String>, ParseError> {
        if let Value::Mapping(setting_map) = setting {
            for (name, config) in setting_map {
                if let (Some(name_str), Value::Mapping(config_map)) = (name.as_str(), config) {
                    if name_str == "priority" {
                        continue;
                    }

                    if let Some(Value::Sequence(aliases)) = config_map.get("aliases") {
                        let aliases: Vec<String> = aliases.iter()
                            .filter_map(|v| v.as_str())
                            .map(|s| s.to_lowercase())
                            .collect();

                        if aliases.contains(&token.to_lowercase()) {
                            return Ok(Some(name_str.to_string()));
                        }
                    }
                }
            }
        }
        Ok(None)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_config() -> Config {
        Config::load_from_file("src/contest/commands.yaml").unwrap()
    }

    #[test]
    fn test_command_resolution() {
        let config = create_test_config();
        let resolver = NameResolver::new(&config).unwrap();

        // 基本的なコマンド解決
        let result = resolver.resolve("login").unwrap();
        assert_eq!(result.commands, vec!["login"]);

        // エイリアスの解決
        let result = resolver.resolve("auth").unwrap();
        assert_eq!(result.commands, vec!["login"]);

        // 複数のコマンド
        let result = resolver.resolve("login test").unwrap();
        assert_eq!(result.commands, vec!["login", "test"]);
    }

    #[test]
    fn test_argument_resolution() {
        let config = create_test_config();
        let resolver = NameResolver::new(&config).unwrap();

        // 言語の解決
        let result = resolver.resolve("test rs abc001_a").unwrap();
        assert_eq!(result.args.get("language").unwrap(), "rust");

        // サイトの解決
        let result = resolver.resolve("login ac").unwrap();
        assert_eq!(result.args.get("site").unwrap(), "atcoder");

        // 問題IDの解決
        let result = resolver.resolve("test abc001_a").unwrap();
        assert_eq!(result.args.get("problem_id").unwrap(), "abc001_a");
    }

    #[test]
    fn test_priority_resolution() {
        let config = create_test_config();
        let resolver = NameResolver::new(&config).unwrap();

        // 優先度に基づく解決
        let result = resolver.resolve("test abc001 a").unwrap();
        assert_eq!(result.args.get("contest").unwrap(), "abc001");
        assert_eq!(result.args.get("problem").unwrap(), "a");
    }

    #[test]
    fn test_invalid_inputs() {
        let config = create_test_config();
        let resolver = NameResolver::new(&config).unwrap();

        // 無効なコマンド
        assert!(matches!(
            resolver.resolve("invalid"),
            Err(ParseError::InvalidCommand(_))
        ));

        // 空のコマンド
        assert!(matches!(
            resolver.resolve(""),
            Err(ParseError::InvalidCommand(_))
        ));

        // 無効なサイト名
        let result = resolver.resolve("login invalid_site").unwrap();
        assert!(!result.args.contains_key("site"));
    }
} 