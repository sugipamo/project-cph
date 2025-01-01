use std::collections::HashMap;
use serde::Deserialize;
use once_cell::sync::Lazy;

#[derive(Debug, Clone)]
pub struct CommandToken {
    pub command_name: String,
    pub arguments: HashMap<String, String>,
}

#[derive(Debug)]
pub enum TokenizeError {
    NoMatch,
    MultipleMatches(Vec<String>),
    InvalidFormat(String),
    ConfigError(String),
}

impl std::fmt::Display for TokenizeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::NoMatch => write!(f, "マッチするコマンドが見つかりません"),
            Self::MultipleMatches(candidates) => write!(f, "複数のコマンドがマッチします: {:?}", candidates),
            Self::InvalidFormat(msg) => write!(f, "不正なフォーマット: {}", msg),
            Self::ConfigError(msg) => write!(f, "設定エラー: {}", msg),
        }
    }
}

impl std::error::Error for TokenizeError {}

type Result<T> = std::result::Result<T, TokenizeError>;

#[derive(Debug, Deserialize)]
struct TokenPattern {
    commands: Vec<String>,
    ordered: Option<Vec<Vec<String>>>,
    unordered: Option<Vec<Vec<String>>>,
}

#[derive(Debug, Deserialize)]
struct TokenRules {
    commands: HashMap<String, TokenPattern>,
}

#[derive(Debug, Clone, Deserialize)]
struct ConfigEntry {
    aliases: Option<Vec<String>>,
    #[serde(flatten)]
    extra: HashMap<String, serde_yaml::Value>,
}

// 設定ファイルの読み込み
static TOKEN_RULES: Lazy<TokenRules> = Lazy::new(|| {
    let config_str = include_str!("../commands/commands.yaml");
    serde_yaml::from_str(config_str).expect("コマンド設定の読み込みに失敗")
});

static CONFIG: Lazy<serde_yaml::Value> = Lazy::new(|| {
    let config_str = include_str!("../config/config.yaml");
    serde_yaml::from_str(config_str).expect("設定ファイルの読み込みに失敗")
});

#[derive(Debug, Clone, Copy)]
enum ParamType {
    Command,
    Site,
    Language,
}

impl ParamType {
    const PARAMS: &'static [(ParamType, &'static str, &'static str, &'static str)] = &[
        (ParamType::Command, "command", "commands", "commands"),
        (ParamType::Site, "site_id", "sites", "aliases"),
        (ParamType::Language, "language", "languages", "aliases"),
    ];

    fn as_str(&self) -> &'static str {
        Self::PARAMS.iter()
            .find(|(t, _, _, _)| t == self)
            .map(|(_, name, _, _)| name)
            .unwrap()
    }

    fn pattern(&self) -> String {
        format!("{{{}}}", self.as_str())
    }

    fn config_key(&self) -> &'static str {
        Self::PARAMS.iter()
            .find(|(t, _, _, _)| t == self)
            .map(|(_, _, key, _)| key)
            .unwrap()
    }

    fn alias_field(&self) -> &'static str {
        Self::PARAMS.iter()
            .find(|(t, _, _, _)| t == self)
            .map(|(_, _, _, field)| field)
            .unwrap()
    }

    fn all() -> &'static [Self] {
        &[Self::Command, Self::Site, Self::Language]
    }
}

#[derive(Debug, Clone)]
struct NameResolver {
    aliases: HashMap<String, String>,
}

impl NameResolver {
    fn new() -> Self {
        Self {
            aliases: HashMap::new(),
        }
    }

    fn register_alias(&mut self, name: &str, alias: &str) {
        self.aliases.insert(alias.to_string(), name.to_string());
    }

    fn resolve(&self, input: &str) -> Option<String> {
        self.aliases.get(input).cloned()
    }
}

fn build_alias_map(
    value: &serde_yaml::Value,
    key: &str,
    alias_field: &str,
    skip_underscore: bool,
) -> Result<NameResolver> {
    let mut resolver = NameResolver::new();

    if let Some(entries) = value.get(key) {
        for (id, value) in entries.as_mapping().ok_or_else(|| TokenizeError::ConfigError(format!("{} is not a mapping", key)))? {
            let id = id.as_str().ok_or_else(|| TokenizeError::ConfigError(format!("{} id is not a string", key)))?;
            
            if skip_underscore && id.starts_with('_') {
                continue;
            }

            if let Some(aliases) = value.get(alias_field) {
                if let Some(aliases) = aliases.as_sequence() {
                    for alias in aliases {
                        if let Some(alias) = alias.as_str() {
                            resolver.register_alias(id, alias);
                        }
                    }
                }
            }
            resolver.register_alias(id, id);
        }
    }

    Ok(resolver)
}

fn build_alias_map_from_commands(commands: &HashMap<String, TokenPattern>) -> Result<NameResolver> {
    let mut resolver = NameResolver::new();
    for (name, pattern) in commands {
        if name.starts_with('_') {
            continue;
        }
        for cmd in &pattern.commands {
            resolver.register_alias(name, cmd);
        }
    }
    Ok(resolver)
}

fn build_resolvers() -> Result<Vec<NameResolver>> {
    let mut resolvers = Vec::new();

    for &param_type in ParamType::all() {
        let resolver = match param_type {
            ParamType::Command => build_alias_map_from_commands(&TOKEN_RULES.commands)?,
            _ => build_alias_map(&CONFIG, param_type.config_key(), param_type.alias_field(), true)?,
        };
        resolvers.push(resolver);
    }

    Ok(resolvers)
}

// 名前解決器のキャッシュ
static RESOLVERS: Lazy<Result<Vec<NameResolver>>> = Lazy::new(build_resolvers);

impl CommandToken {
    /// コマンド文字列をパースしてコマンド種別とパラメータを抽出
    pub fn parse(input: &str) -> Result<Self> {
        let args: Vec<&str> = input.split_whitespace().collect();
        if args.is_empty() {
            return Err(TokenizeError::InvalidFormat("空のコマンドです".to_string()));
        }

        // 名前解決器の取得
        let resolvers = RESOLVERS.as_ref()
            .map_err(|e| TokenizeError::ConfigError(format!("名前解決器の初期化に失敗: {}", e)))?;

        // コマンド候補の収集
        let mut command_candidates = Vec::new();
        for arg in &args {
            for resolver in &resolvers {
                if let Some(cmd_type) = resolver.resolve(arg) {
                    command_candidates.push((*arg, cmd_type));
                }
            }
        }

        if command_candidates.is_empty() {
            return Err(TokenizeError::NoMatch);
        }

        // 各コマンド候補に対してパターンマッチを試みる
        let mut results = Vec::new();
        for (cmd_arg, cmd_type) in command_candidates {
            let pattern = &TOKEN_RULES.commands[&cmd_type];
            
            // 順序固定パターンを優先的にチェック
            if let Some(ordered_patterns) = &pattern.ordered {
                for ordered_pattern in ordered_patterns {
                    if let Some(params) = try_match_ordered(&args, cmd_arg, ordered_pattern, &resolvers[0]) {
                        results.push((cmd_type.clone(), params));
                    }
                }
            }

            // 順序不定パターンをチェック
            if let Some(unordered_patterns) = &pattern.unordered {
                for unordered_pattern in unordered_patterns {
                    if let Some(params) = try_match_unordered(&args, cmd_arg, unordered_pattern, &resolvers[0]) {
                        results.push((cmd_type.clone(), params));
                    }
                }
            }
        }

        match results.len() {
            0 => Err(TokenizeError::NoMatch),
            1 => {
                let (command_type, parameters) = results.into_iter().next().unwrap();
                Ok(CommandToken {
                    command_name: command_type,
                    arguments: parameters,
                })
            }
            _ => {
                let candidates: Vec<String> = results
                    .into_iter()
                    .map(|(cmd_type, _)| cmd_type)
                    .collect();
                Err(TokenizeError::MultipleMatches(candidates))
            }
        }
    }
}

fn try_match_ordered(
    args: &[&str],
    cmd_arg: &str,
    pattern: &[String],
    resolvers: &[NameResolver],
) -> Option<HashMap<String, String>> {
    let mut params = HashMap::new();
    let mut pattern_idx = 0;
    let mut arg_idx = 0;

    // パターンの長さと引数の長さが一致しない場合はマッチしない
    if args.len() != pattern.len() {
        return None;
    }

    while arg_idx < args.len() && pattern_idx < pattern.len() {
        let arg = args[arg_idx];
        let param_type = &pattern[pattern_idx];

        let mut matched = false;
        for (i, &param) in ParamType::all().iter().enumerate() {
            if param_type == &param.pattern() {
                match param {
                    ParamType::Command => {
                        if arg != cmd_arg {
                            return None;
                        }
                        matched = true;
                    }
                    _ => {
                        if let Some(value) = resolvers[i].resolve(arg) {
                            params.insert(param.as_str().to_string(), value);
                            matched = true;
                        }
                    }
                }
                break;
            }
        }

        if !matched {
            return None;
        }

        arg_idx += 1;
        pattern_idx += 1;
    }

    if pattern_idx == pattern.len() {
        Some(params)
    } else {
        None
    }
}

fn try_match_unordered(
    args: &[&str],
    cmd_arg: &str,
    pattern: &[String],
    resolvers: &[NameResolver],
) -> Option<HashMap<String, String>> {
    let mut params = HashMap::new();
    let mut used_args = vec![false; args.len()];
    let mut matched_params = 0;

    // パターンの長さと引数の長さが一致しない場合はマッチしない
    if args.len() != pattern.len() {
        return None;
    }

    // コマンド引数を探す
    let mut found_command = false;
    for (i, &arg) in args.iter().enumerate() {
        if arg == cmd_arg {
            used_args[i] = true;
            found_command = true;
            matched_params += 1;
            break;
        }
    }
    if !found_command {
        return None;
    }

    // 各パラメータタイプに対して、マッチする引数を探す
    for param_type in pattern {
        if param_type == &ParamType::Command.pattern() {
            continue;
        }

        let mut found = false;
        for (i, &arg) in args.iter().enumerate() {
            if used_args[i] {
                continue;
            }

            for (j, &param) in ParamType::all().iter().enumerate() {
                if param_type == &param.pattern() {
                    if let Some(value) = resolvers[j].resolve(arg) {
                        params.insert(param.as_str().to_string(), value);
                        used_args[i] = true;
                        found = true;
                        matched_params += 1;
                        break;
                    }
                }
            }
            if found {
                break;
            }
        }
        if !found {
            return None;
        }
    }

    if matched_params == pattern.len() {
        Some(params)
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resolver_initialization() {
        let resolvers = RESOLVERS.as_ref().unwrap();

        // コマンドの解決
        assert!(resolvers[0].aliases.contains_key("test"));
        assert!(resolvers[0].aliases.contains_key("t"));
        assert!(resolvers[0].aliases.contains_key("check"));

        // サイトの解決
        assert!(resolvers[1].aliases.contains_key("atcoder"));
        assert!(resolvers[1].aliases.contains_key("ac"));

        // 言語の解決
        assert!(resolvers[2].aliases.contains_key("rust"));
        assert!(resolvers[2].aliases.contains_key("rs"));
    }

    #[test]
    fn test_basic_command() {
        let input = "test abc123";
        let result = CommandToken::parse(input).unwrap();
        assert_eq!(result.command_name, "test");
        assert_eq!(result.arguments["problem_id"], "abc123");
    }

    #[test]
    fn test_command_with_underscore() {
        let input = "test abc_123";
        let result = CommandToken::parse(input).unwrap();
        assert_eq!(result.command_name, "test");
        assert_eq!(result.arguments["problem_id"], "abc_123");
    }

    #[test]
    fn test_command_with_site() {
        let input = "atcoder test abc123";
        let result = CommandToken::parse(input).unwrap();
        assert_eq!(result.command_name, "test");
        assert_eq!(result.arguments["site_id"], "atcoder");
        assert_eq!(result.arguments["problem_id"], "abc123");
    }

    #[test]
    fn test_command_with_contest() {
        let inputs = vec![
            ("test abc123_d", "abc123", "d"),
            ("test abc123 d", "abc123", "d"),
        ];

        for (input, expected_contest, expected_problem) in inputs {
            let result = CommandToken::parse(input).unwrap();
            assert_eq!(result.command_name, "test");
            assert_eq!(result.arguments["contest_id"], expected_contest, "入力: {}", input);
            assert_eq!(result.arguments["problem_id"], expected_problem, "入力: {}", input);
        }
    }

    #[test]
    fn test_command_aliases() {
        for cmd in ["test", "t", "check"] {
            let input = format!("{} abc123", cmd);
            let result = CommandToken::parse(&input).unwrap();
            assert_eq!(result.command_name, "test");
            assert_eq!(result.arguments["problem_id"], "abc123");
        }
    }

    #[test]
    fn test_multiple_matches() {
        let inputs = &[
            "test abc123 d",
            "test abc123_d",
        ];

        for input in inputs {
            if let Err(TokenizeError::MultipleMatches(candidates)) = CommandToken::parse(input) {
                assert!(candidates.contains(&"test".to_string()));
                assert!(candidates.len() > 1, "入力 '{}' に対して複数の候補が見つかるべきです", input);
            } else {
                panic!("入力 '{}' に対して複数マッチエラーが発生するべきです", input);
            }
        }
    }

    #[test]
    fn test_invalid_command() {
        let input = "invalid xyz";
        assert!(matches!(CommandToken::parse(input), Err(TokenizeError::NoMatch)));
    }

    #[test]
    fn test_empty_command() {
        let input = "";
        assert!(matches!(
            CommandToken::parse(input),
            Err(TokenizeError::InvalidFormat(_))
        ));
    }

    #[test]
    fn test_command_with_extra_spaces() {
        let input = "  test   abc123  ";
        let result = CommandToken::parse(input).unwrap();
        assert_eq!(result.command_name, "test");
        assert_eq!(result.arguments["problem_id"], "abc123");
    }

    #[test]
    fn test_command_case_sensitivity() {
        let input = "TEST abc123";
        assert!(matches!(CommandToken::parse(input), Err(TokenizeError::NoMatch)));
    }

    #[test]
    fn test_command_unordered() {
        let test_cases = vec![
            ("abc123 test", "test"),
            ("abc123 t", "test"),
            ("abc123 check", "test"),
        ];

        for (input, expected_type) in test_cases {
            let result = CommandToken::parse(input).unwrap();
            assert_eq!(result.command_name, expected_type);
        }
    }

    #[test]
    fn test_command_with_all_parameters() {
        let input = "atcoder test abc123 d";
        let result = CommandToken::parse(input).unwrap();
        assert_eq!(result.command_name, "test");
        assert_eq!(result.arguments["site_id"], "atcoder");
        assert_eq!(result.arguments["problem_id"], "abc123");
    }

    #[test]
    fn test_command_with_site_alias() {
        let inputs = &[
            "atcoder test abc123",
            "ac test abc123",
        ];

        for input in inputs {
            let result = CommandToken::parse(input).unwrap();
            assert_eq!(result.command_name, "test");
            assert!(result.arguments.contains_key("problem_id"));
        }
    }
} 