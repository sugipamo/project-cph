use std::collections::HashMap;
use crate::config::{Config, ConfigAccess, ConfigNode};
use anyhow::{Result, anyhow};

#[derive(Debug, Clone)]
pub struct ResolvedCommand {
    pub commands: Vec<String>,
    pub args: HashMap<String, String>,
}

pub struct CommandResolver {
    config: Config,
}

impl CommandResolver {
    pub fn new(config: &Config) -> Result<Self> {
        Ok(Self {
            config: config.clone(),
        })
    }

    fn get_executions(&self) -> Result<Vec<String>> {
        let executions = self.config.get_all("executions")?
            .into_iter()
            .filter_map(|node| node.as_typed::<String>().ok())
            .collect();
        Ok(executions)
    }

    fn get_settings(&self) -> Result<HashMap<String, String>> {
        let settings = self.config.get_all("settings")?
            .into_iter()
            .filter_map(|node| {
                let key = node.key().ok()?;
                let value = node.as_typed::<String>().ok()?;
                Some((key, value))
            })
            .collect();
        Ok(settings)
    }

    fn get_aliases(&self, command: &str) -> Result<Option<String>> {
        let aliases: ConfigNode = self.config.get("aliases")?;
        let alias = aliases.as_typed::<HashMap<String, String>>()
            .ok()
            .and_then(|map| map.get(command).cloned());
        Ok(alias)
    }

    pub fn parse_command(&self, tokens: &[&str]) -> Result<(CommandType, HashMap<String, String>)> {
        if tokens.is_empty() {
            return Err(anyhow!("コマンドが空です"));
        }

        let command = tokens[0].to_lowercase();
        let args = tokens[1..].iter().map(|s| s.to_string()).collect::<Vec<_>>();

        match command.as_str() {
            "test" => self.parse_test_command(&args),
            "login" => self.parse_login_command(&args),
            _ => Err(anyhow!("未知のコマンド: {}", command)),
        }
    }

    pub fn resolve(&self, input: &str) -> Result<ResolvedCommand> {
        let tokens: Vec<_> = input.split_whitespace().collect();
        if tokens.is_empty() {
            return Err(anyhow!("コマンドが空です"));
        }

        let (command_type, args) = self.parse_command(&tokens)?;
        let mut resolved = ResolvedCommand {
            commands: vec![],
            args,
        };

        match command_type {
            CommandType::Test => {
                resolved.commands.push("test".to_string());
            }
            CommandType::Login => {
                resolved.commands.push("login".to_string());
            }
        }

        Ok(resolved)
    }

    fn parse_test_command(&self, args: &[String]) -> Result<(CommandType, HashMap<String, String>)> {
        let mut command_args = HashMap::new();
        
        if args.is_empty() {
            return Err(anyhow!("テストコマンドには引数が必要です"));
        }

        // 言語の解析
        if let Some(language) = args.first() {
            match language.to_lowercase().as_str() {
                "rs" | "rust" => { command_args.insert("language".to_string(), "rust".to_string()); }
                "py" | "python" | "python3" => { command_args.insert("language".to_string(), "python".to_string()); }
                _ => {}
            }
        }

        // コンテストIDと問題IDの解析
        if args.len() >= 3 {
            command_args.insert("contest".to_string(), args[1].clone());
            command_args.insert("problem".to_string(), args[2].clone());
        } else if args.len() == 2 {
            command_args.insert("problem_id".to_string(), args[1].clone());
        }

        Ok((CommandType::Test, command_args))
    }

    fn parse_login_command(&self, args: &[String]) -> Result<(CommandType, HashMap<String, String>)> {
        let mut command_args = HashMap::new();
        
        if let Some(site) = args.first() {
            match site.to_lowercase().as_str() {
                "ac" | "atcoder" | "at-coder" => {
                    command_args.insert("site".to_string(), "atcoder".to_string());
                }
                _ => {}
            }
        }

        Ok((CommandType::Login, command_args))
    }
}

#[derive(Debug, PartialEq)]
pub enum CommandType {
    Test,
    Login,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_command_resolution() {
        let config = Config::default();
        let resolver = CommandResolver::new(&config).unwrap();

        let result = resolver.resolve("login").unwrap();
        assert_eq!(result.commands, vec!["login"]);
    }

    #[test]
    fn test_alias_resolution() {
        let config = Config::default();
        let resolver = CommandResolver::new(&config).unwrap();

        let result = resolver.resolve("auth").unwrap();
        assert_eq!(result.commands, vec!["login"]);

        let result = resolver.resolve("o").unwrap();
        assert_eq!(result.commands, vec!["open"]);
    }

    #[test]
    fn test_command_with_args() {
        let config = Config::default();
        let resolver = CommandResolver::new(&config).unwrap();

        let result = resolver.resolve("login test").unwrap();
        assert_eq!(result.commands, vec!["login", "test"]);
    }

    #[test]
    fn test_language_normalization() {
        let config = Config::default();
        let resolver = CommandResolver::new(&config).unwrap();

        let result = resolver.resolve("test rs abc001 a").unwrap();
        assert_eq!(result.args.get("language").unwrap(), "rust");

        let result = resolver.resolve("test RUST abc001 a").unwrap();
        assert_eq!(result.args.get("language").unwrap(), "rust");

        let result = resolver.resolve("test python3 abc001 a").unwrap();
        assert_eq!(result.args.get("language").unwrap(), "python");
    }

    #[test]
    fn test_site_normalization() {
        let config = Config::default();
        let resolver = CommandResolver::new(&config).unwrap();

        let result = resolver.resolve("login ac").unwrap();
        assert_eq!(result.args.get("site").unwrap(), "atcoder");

        let result = resolver.resolve("login at-coder").unwrap();
        assert_eq!(result.args.get("site").unwrap(), "atcoder");
    }

    #[test]
    fn test_contest_problem_parsing() {
        let config = Config::default();
        let resolver = CommandResolver::new(&config).unwrap();

        let result = resolver.resolve("test abc001 a").unwrap();
        assert!(result.args.contains_key("contest"));
        assert!(result.args.contains_key("problem"));
        assert_eq!(result.args.get("contest").unwrap(), "abc001");
        assert_eq!(result.args.get("problem").unwrap(), "a");

        let result = resolver.resolve("test other_format").unwrap();
        assert_eq!(result.args.get("problem_id").unwrap(), "other_format");
    }

    #[test]
    fn test_contest_id_extraction() {
        let config = Config::default();
        let resolver = CommandResolver::new(&config).unwrap();

        let result = resolver.resolve("test abc001 a").unwrap();
        assert_eq!(result.args.get("contest").unwrap(), "abc001");
    }

    #[test]
    fn test_problem_id_extraction() {
        let config = Config::default();
        let resolver = CommandResolver::new(&config).unwrap();

        let result = resolver.resolve("test abc001 a").unwrap();
        assert_eq!(result.args.get("problem").unwrap(), "a");
    }

    #[test]
    fn test_full_command_parsing() {
        let config = Config::default();
        let resolver = CommandResolver::new(&config).unwrap();

        let result = resolver.resolve("test rs abc001 a").unwrap();
        assert!(result.args.contains_key("language"));
        assert!(result.args.contains_key("contest"));
        assert!(result.args.contains_key("problem"));
    }

    mod error_tests {
        use super::*;

        #[test]
        fn test_invalid_command_format() {
            let config = Config::default();
            let resolver = CommandResolver::new(&config).unwrap();

            let result = resolver.resolve("");
            assert!(result.is_err());
        }

        #[test]
        fn test_unknown_command() {
            let config = Config::default();
            let resolver = CommandResolver::new(&config).unwrap();

            let result = resolver.resolve("unknown_command");
            assert!(result.is_err());
        }

        #[test]
        fn test_invalid_site() {
            let config = Config::default();
            let resolver = CommandResolver::new(&config).unwrap();

            let result = resolver.resolve("login invalid_site").unwrap();
            assert!(!result.args.contains_key("site"));
        }

        #[test]
        fn test_invalid_language() {
            let config = Config::default();
            let resolver = CommandResolver::new(&config).unwrap();

            let result = resolver.resolve("test invalid_lang abc001_a").unwrap();
            assert!(!result.args.contains_key("language"));
        }
    }
} 