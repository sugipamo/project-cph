use std::error::Error;
use std::collections::HashMap;
use serde_yaml::Value;
use crate::config::{Config, ConfigError, ConfigType};

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
    MissingSection(String),
    EmptyCommand,
    UnknownCommand(String),
}

impl std::fmt::Display for ParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ParseError::InvalidCommand(msg) => write!(f, "無効なコマンド: {}", msg),
            ParseError::ConfigError(err) => write!(f, "設定エラー: {}", err),
            ParseError::MissingSection(msg) => write!(f, "設定セクションが見つかりません: {}", msg),
            ParseError::EmptyCommand => write!(f, "コマンドが空です"),
            ParseError::UnknownCommand(cmd) => write!(f, "未知のコマンド: {}", cmd),
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
                expected: ConfigType::StringArray,
                actual: ConfigType::Null,
            }))
        }
    }

    fn try_resolve_setting(
        &self,
        setting: &Value,
        token: &str,
    ) -> Result<Option<String>, ParseError> {
        if let Value::Mapping(setting_map) = setting {
            // 設定の種類を判断
            let has_priority = setting_map.contains_key("priority");
            let has_inner_settings = setting_map.values().any(|v| {
                if let Value::Mapping(m) = v {
                    m.contains_key("aliases")
                } else {
                    false
                }
            });

            if has_priority && !has_inner_settings {
                // コンテストと問題の場合は直接トークンをマッチング
                return Ok(Some(token.to_string()));
            } else {
                // 言語とサイトの場合はエイリアスをチェック
                for (name, config) in setting_map {
                    if let Value::Mapping(config_map) = config {
                        if let Some(Value::Sequence(aliases)) = config_map.get("aliases") {
                            let aliases: Vec<String> = aliases.iter()
                                .filter_map(|v| v.as_str())
                                .map(|s| s.to_lowercase())
                                .collect();

                            if aliases.contains(&token.to_lowercase()) {
                                return Ok(Some(name.as_str().unwrap_or_default().to_string()));
                            }
                        }
                    }
                }
            }
        }
        Ok(None)
    }

    pub fn parse_command(&self, tokens: &[&str]) -> Result<(CommandType, HashMap<String, String>), ParseError> {
        if tokens.is_empty() {
            return Err(ParseError::EmptyCommand);
        }

        let mut current_pos = 0;
        let command_type = if let Some(command_type) = self.command_aliases.get(tokens[0]) {
            current_pos += 1;
            command_type.clone()
        } else {
            return Err(ParseError::UnknownCommand(tokens[0].to_string()));
        };

        // 残りのトークンを収集
        let remaining_tokens: Vec<String> = tokens[current_pos..].iter().map(|&s| s.to_string()).collect();
        let mut args = HashMap::new();

        // 言語とサイトの解決
        for (i, token) in remaining_tokens.iter().enumerate() {
            for (setting_name, setting_value) in &self.settings {
                if setting_name == "contest" || setting_name == "problem" {
                    continue;
                }

                if let Some(resolved_value) = self.try_resolve_setting(
                    setting_value,
                    token,
                )? {
                    args.insert(setting_name.clone(), resolved_value);
                    break;
                }
            }
        }

        Ok((command_type, args))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_config() -> Config {
        Config::load_from_file("src/contest/commands.yaml").unwrap()
    }

    mod command_tests {
        use super::*;

        #[test]
        fn test_single_command() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            let result = resolver.resolve("login").unwrap();
            assert_eq!(result.commands, vec!["login"]);
        }

        #[test]
        fn test_command_alias() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            let result = resolver.resolve("auth").unwrap();
            assert_eq!(result.commands, vec!["login"]);

            let result = resolver.resolve("o").unwrap();
            assert_eq!(result.commands, vec!["open"]);
        }

        #[test]
        fn test_multiple_commands() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            let result = resolver.resolve("login test").unwrap();
            assert_eq!(result.commands, vec!["login", "test"]);
        }
    }

    mod argument_tests {
        use super::*;

        #[test]
        fn test_language_resolution() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            // 基本的な言語解決
            let result = resolver.resolve("test rs abc001 a").unwrap();
            assert_eq!(result.args.get("language").unwrap(), "rust");

            // 大文字小文字の違いを無視
            let result = resolver.resolve("test RUST abc001 a").unwrap();
            assert_eq!(result.args.get("language").unwrap(), "rust");

            // 別のエイリアス
            let result = resolver.resolve("test python3 abc001 a").unwrap();
            assert_eq!(result.args.get("language").unwrap(), "python");
        }

        #[test]
        fn test_site_resolution() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            // 基本的なサイト解決
            let result = resolver.resolve("login ac").unwrap();
            assert_eq!(result.args.get("site").unwrap(), "atcoder");

            // エイリアスの解決
            let result = resolver.resolve("login at-coder").unwrap();
            assert_eq!(result.args.get("site").unwrap(), "atcoder");
        }

        #[test]
        fn test_problem_id_resolution() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            // コンテストと問題の形式
            let result = resolver.resolve("test abc001 a").unwrap();
            assert!(result.args.contains_key("contest"));
            assert!(result.args.contains_key("problem"));
            assert_eq!(result.args.get("contest").unwrap(), "abc001");
            assert_eq!(result.args.get("problem").unwrap(), "a");

            // 未解決の場合は問題IDとして扱う
            let result = resolver.resolve("test other_format").unwrap();
            assert_eq!(result.args.get("problem_id").unwrap(), "other_format");
        }
    }

    mod priority_tests {
        use super::*;

        #[test]
        fn test_contest_priority() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            let result = resolver.resolve("test abc001 a").unwrap();
            assert_eq!(result.args.get("contest").unwrap(), "abc001");
        }

        #[test]
        fn test_problem_priority() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            let result = resolver.resolve("test abc001 a").unwrap();
            assert_eq!(result.args.get("problem").unwrap(), "a");
        }

        #[test]
        fn test_multiple_settings_priority() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            let result = resolver.resolve("test rs abc001 a").unwrap();
            assert!(result.args.contains_key("language"));
            assert!(result.args.contains_key("contest"));
            assert!(result.args.contains_key("problem"));
        }
    }

    mod error_tests {
        use super::*;

        #[test]
        fn test_empty_input() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            assert!(matches!(
                resolver.resolve(""),
                Err(ParseError::InvalidCommand(_))
            ));
        }

        #[test]
        fn test_invalid_command() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            assert!(matches!(
                resolver.resolve("invalid"),
                Err(ParseError::InvalidCommand(_))
            ));
        }

        #[test]
        fn test_invalid_site() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            let result = resolver.resolve("login invalid_site").unwrap();
            assert!(!result.args.contains_key("site"));
        }

        #[test]
        fn test_invalid_language() {
            let config = create_test_config();
            let resolver = NameResolver::new(&config).unwrap();

            let result = resolver.resolve("test invalid_lang abc001_a").unwrap();
            assert!(!result.args.contains_key("language"));
        }
    }
} 