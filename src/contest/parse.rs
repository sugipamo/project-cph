use std::collections::HashMap;
use crate::config::{Config, FromConfigValue};
use crate::contest::model::{Command, CommandContext};
use anyhow::{Result, anyhow};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct CommandConfig {
    pub executions: HashMap<String, CommandAliases>,
    pub settings: CommandSettings,
}

#[derive(Debug, Deserialize)]
pub struct CommandAliases {
    pub aliases: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct CommandSettings {
    pub contest: SettingPriority,
    pub problem: SettingPriority,
    pub language: HashMap<String, LanguageConfig>,
    pub site: HashMap<String, SiteConfig>,
}

#[derive(Debug, Deserialize)]
pub struct SettingPriority {
    pub priority: i32,
}

#[derive(Debug, Deserialize)]
pub struct LanguageConfig {
    pub aliases: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct SiteConfig {
    pub aliases: Vec<String>,
}

impl FromConfigValue for CommandConfig {
    fn from_config_value(value: &serde_yaml::Value) -> Result<Self> {
        serde_yaml::from_value(value.clone())
            .map_err(|e| anyhow!("CommandConfigへの変換に失敗: {}", e))
    }
}

pub struct CommandParser {
    config: CommandConfig,
}

impl CommandParser {
    pub fn new(config: &Config) -> Result<Self> {
        let config: CommandConfig = config.get("commands")?;
        Ok(Self { config })
    }

    pub fn parse(&self, input: &str) -> Result<CommandContext> {
        let tokens: Vec<_> = input.split_whitespace().collect();
        if tokens.is_empty() {
            return Err(anyhow!("コマンドが空です"));
        }

        let command = self.resolve_command(&tokens[0].to_lowercase())?;
        let args = &tokens[1..];

        let command = match command.as_str() {
            "login" => Command::Login,
            "open" => self.parse_open_command(args)?,
            "test" => self.parse_test_command(args)?,
            "submit" => Command::Submit,
            _ => return Err(anyhow!("未知のコマンド: {}", command)),
        };

        Ok(CommandContext::new(command))
    }

    fn resolve_command(&self, cmd: &str) -> Result<String> {
        for (name, aliases) in &self.config.executions {
            if name == cmd || aliases.aliases.iter().any(|a| a == cmd) {
                return Ok(name.clone());
            }
        }
        Err(anyhow!("未知のコマンド: {}", cmd))
    }

    fn resolve_site(&self, site: &str) -> Result<String> {
        for (name, config) in &self.config.settings.site {
            if name == site || config.aliases.iter().any(|a| a == site) {
                return Ok(name.clone());
            }
        }
        Err(anyhow!("未知のサイト: {}", site))
    }

    fn parse_open_command(&self, args: &[&str]) -> Result<Command> {
        if args.is_empty() {
            return Err(anyhow!("サイトの指定が必要です"));
        }

        let site = self.resolve_site(&args[0].to_lowercase())?;
        let (contest_id, problem_id) = match args.len() {
            1 => (None, None),
            2 => (Some(args[1].to_string()), None),
            3 => (Some(args[1].to_string()), Some(args[2].to_string())),
            _ => return Err(anyhow!("引数が多すぎます")),
        };

        Ok(Command::Open {
            site,
            contest_id,
            problem_id,
        })
    }

    fn parse_test_command(&self, args: &[&str]) -> Result<Command> {
        let test_number = match args.first() {
            Some(num) => match num.parse() {
                Ok(n) => Some(n),
                Err(_) => None,
            },
            None => None,
        };

        Ok(Command::Test { test_number })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_config() -> Config {
        let yaml = r#"
        commands:
          executions:
            login:
              aliases: ["auth"]
            open:
              aliases: ["o", "show"]
            test:
              aliases: ["t", "check"]
            submit:
              aliases: ["s", "sub"]
          settings:
            contest:
              priority: 2
            problem:
              priority: 1
            language:
              rust:
                aliases: ["rs", "Rust", "RUST"]
              python:
                aliases: ["python", "python3"]
              pypy:
                aliases: ["pypy", "py", "pypy3"]
              cpp:
                aliases: ["cpp", "c++", "gcc"]
            site:
              atcoder:
                aliases: ["ac", "at-coder", "at_coder"]
        "#;
        Config::from_str(yaml).unwrap()
    }

    #[test]
    fn test_parse_login() {
        let config = create_test_config();
        let parser = CommandParser::new(&config).unwrap();

        let result = parser.parse("login").unwrap();
        assert!(matches!(result.command, Command::Login));

        let result = parser.parse("auth").unwrap();
        assert!(matches!(result.command, Command::Login));
    }

    #[test]
    fn test_parse_open() {
        let config = create_test_config();
        let parser = CommandParser::new(&config).unwrap();

        let result = parser.parse("open atcoder abc001 a").unwrap();
        if let Command::Open { site, contest_id, problem_id } = result.command {
            assert_eq!(site, "atcoder");
            assert_eq!(contest_id, Some("abc001".to_string()));
            assert_eq!(problem_id, Some("a".to_string()));
        } else {
            panic!("Expected Open command");
        }
    }

    #[test]
    fn test_parse_test() {
        let config = create_test_config();
        let parser = CommandParser::new(&config).unwrap();

        let result = parser.parse("test 1").unwrap();
        if let Command::Test { test_number } = result.command {
            assert_eq!(test_number, Some(1));
        } else {
            panic!("Expected Test command");
        }

        let result = parser.parse("test").unwrap();
        if let Command::Test { test_number } = result.command {
            assert_eq!(test_number, None);
        } else {
            panic!("Expected Test command");
        }
    }

    #[test]
    fn test_parse_submit() {
        let config = create_test_config();
        let parser = CommandParser::new(&config).unwrap();

        let result = parser.parse("submit").unwrap();
        assert!(matches!(result.command, Command::Submit));

        let result = parser.parse("s").unwrap();
        assert!(matches!(result.command, Command::Submit));
    }
} 