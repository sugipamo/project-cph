use std::collections::HashMap;
use serde::Deserialize;
use once_cell::sync::Lazy;

#[derive(Debug, Clone)]
pub struct ParsedCommand {
    pub command_type: String,
    pub parameters: HashMap<String, String>,
}

#[derive(Debug)]
pub enum ParseError {
    NoMatch,
    MultipleMatches(Vec<String>),
    InvalidFormat(String),
}

type Result<T> = std::result::Result<T, ParseError>;

#[derive(Debug, Deserialize)]
struct CommandPattern {
    commands: Vec<String>,
    ordered: Option<Vec<Vec<String>>>,
    unordered: Option<Vec<Vec<String>>>,
}

#[derive(Debug, Deserialize)]
struct CommandsConfig {
    commands: HashMap<String, CommandPattern>,
}

// コマンド設定をグローバルで1回だけ読み込む
static COMMANDS_CONFIG: Lazy<CommandsConfig> = Lazy::new(|| {
    let config_str = include_str!("../commands/commands.yaml");
    serde_yaml::from_str(config_str).expect("コマンド設定の読み込みに失敗")
});

// コマンド名から対応するパターンへの逆引きマップ
static COMMAND_LOOKUP: Lazy<HashMap<String, Vec<(String, &'static CommandPattern)>>> = Lazy::new(|| {
    let mut lookup = HashMap::new();
    for (cmd_type, pattern) in &COMMANDS_CONFIG.commands {
        for cmd_name in &pattern.commands {
            lookup.entry(cmd_name.clone())
                .or_insert_with(Vec::new)
                .push((cmd_type.clone(), pattern));
        }
    }
    lookup
});

impl ParsedCommand {
    /// コマンド文字列をパースしてコマンド種別とパラメータを抽出
    pub fn parse(input: &str) -> Result<Self> {
        let args: Vec<&str> = input.split_whitespace().collect();
        if args.is_empty() {
            return Err(ParseError::InvalidFormat("空のコマンドです".to_string()));
        }

        let mut matches = Vec::new();

        // コマンド名を含む引数を探す
        for &arg in &args {
            if let Some(patterns) = COMMAND_LOOKUP.get(arg) {
                for (cmd_type, pattern) in patterns {
                    if let Some(matched) = Self::try_match_command(&args, pattern)? {
                        matches.push((cmd_type.clone(), matched));
                    }
                }
            }
        }

        match matches.len() {
            0 => Err(ParseError::NoMatch),
            1 => {
                let (command_type, parameters) = matches.into_iter().next().unwrap();
                Ok(ParsedCommand {
                    command_type,
                    parameters,
                })
            }
            _ => {
                let candidates: Vec<String> = matches.into_iter()
                    .map(|(cmd_type, _)| cmd_type)
                    .collect();
                Err(ParseError::MultipleMatches(candidates))
            }
        }
    }

    /// コマンドパターンとのマッチングを試行
    fn try_match_command(
        args: &[&str],
        pattern: &CommandPattern,
    ) -> Result<Option<HashMap<String, String>>> {
        // コマンド名のマッチング
        let command_pos = args.iter().position(|&arg| {
            pattern.commands.iter().any(|cmd| cmd == arg)
        });

        let Some(cmd_pos) = command_pos else {
            return Ok(None);
        };

        // orderedパターンのマッチング
        if let Some(ordered_patterns) = &pattern.ordered {
            for pattern_args in ordered_patterns {
                if let Some(params) = Self::try_match_ordered(args, cmd_pos, pattern_args) {
                    return Ok(Some(params));
                }
            }
        }

        // unorderedパターンのマッチング
        if let Some(unordered_patterns) = &pattern.unordered {
            for pattern_args in unordered_patterns {
                if let Some(params) = Self::try_match_unordered(args, cmd_pos, pattern_args) {
                    return Ok(Some(params));
                }
            }
        }

        Ok(None)
    }

    /// 順序付きパターンのマッチング
    fn try_match_ordered(
        args: &[&str],
        cmd_pos: usize,
        pattern: &[String],
    ) -> Option<HashMap<String, String>> {
        let mut params = HashMap::new();
        let mut pattern_pos = 0;
        let mut arg_pos = 0;

        while pattern_pos < pattern.len() && arg_pos < args.len() {
            let pattern_arg = &pattern[pattern_pos];
            let arg = args[arg_pos];

            if pattern_arg.starts_with('{') && pattern_arg.ends_with('}') {
                let param_name = &pattern_arg[1..pattern_arg.len() - 1];
                if param_name == "command" {
                    if arg_pos != cmd_pos {
                        return None;
                    }
                } else {
                    params.insert(param_name.to_string(), arg.to_string());
                }
                pattern_pos += 1;
            }
            arg_pos += 1;
        }

        if pattern_pos == pattern.len() {
            Some(params)
        } else {
            None
        }
    }

    /// 順序なしパターンのマッチング
    fn try_match_unordered(
        args: &[&str],
        cmd_pos: usize,
        pattern: &[String],
    ) -> Option<HashMap<String, String>> {
        let mut params = HashMap::new();
        let mut used_args = vec![false; args.len()];
        used_args[cmd_pos] = true;

        for pattern_arg in pattern {
            if pattern_arg.starts_with('{') && pattern_arg.ends_with('}') {
                let param_name = &pattern_arg[1..pattern_arg.len() - 1];
                if param_name == "command" {
                    continue;
                }

                let mut found = false;
                for (i, &arg) in args.iter().enumerate() {
                    if !used_args[i] {
                        params.insert(param_name.to_string(), arg.to_string());
                        used_args[i] = true;
                        found = true;
                        break;
                    }
                }

                if !found {
                    return None;
                }
            }
        }

        Some(params)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_test_command() {
        let input = "test abc_123";
        let result = ParsedCommand::parse(input).unwrap();
        assert_eq!(result.command_type, "test");
        assert_eq!(result.parameters["problem_id"], "abc_123");
    }

    #[test]
    fn test_parse_with_site() {
        let input = "atcoder test abc_123";
        let result = ParsedCommand::parse(input).unwrap();
        assert_eq!(result.command_type, "test");
        assert_eq!(result.parameters["site_id"], "atcoder");
        assert_eq!(result.parameters["problem_id"], "abc_123");
    }

    #[test]
    fn test_parse_unordered() {
        let input = "abc_123 test abc";
        let result = ParsedCommand::parse(input).unwrap();
        assert_eq!(result.command_type, "test");
        assert_eq!(result.parameters["contest_id"], "abc");
        assert_eq!(result.parameters["problem_id"], "abc_123");
    }

    #[test]
    fn test_invalid_command() {
        let input = "invalid xyz";
        assert!(matches!(ParsedCommand::parse(input), Err(ParseError::NoMatch)));
    }
} 