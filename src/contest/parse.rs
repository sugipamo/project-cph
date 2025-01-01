use std::collections::HashMap;
use serde::Deserialize;
use once_cell::sync::Lazy;

// 識別子の種類を定義
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IdentifierType {
    Command,
    Site,
    Language,
}

// 識別子の種類の定数を定義
pub const IDENTIFIER_TYPES: &[IdentifierType] = &[
    IdentifierType::Command,
    IdentifierType::Site,
    IdentifierType::Language,
];

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

// 設定ファイルの読み込み
static TOKEN_RULES: Lazy<TokenRules> = Lazy::new(|| {
    let config_str = include_str!("../commands/commands.yaml");
    serde_yaml::from_str(config_str).expect("コマンド設定の読み込みに失敗")
});

static CONFIG: Lazy<serde_yaml::Value> = Lazy::new(|| {
    let config_str = include_str!("../config/config.yaml");
    serde_yaml::from_str(config_str).expect("設定ファイルの読み込みに失敗")
});

#[derive(Debug, Clone, Deserialize)]
struct ConfigEntry {
    aliases: Option<Vec<String>>,
    #[serde(flatten)]
    extra: serde_yaml::Value,
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

fn build_resolvers() -> Result<(NameResolver, NameResolver, NameResolver)> {
    let mut command_resolver = NameResolver::new();
    let mut site_resolver = NameResolver::new();
    let mut language_resolver = NameResolver::new();

    // コマンドのエイリアス
    for (name, pattern) in &TOKEN_RULES.commands {
        for cmd in &pattern.commands {
            command_resolver.register_alias(name, cmd);
        }
    }

    // サイトのエイリアス
    if let Some(sites) = CONFIG.get("sites") {
        for (site_id, value) in sites.as_mapping().ok_or_else(|| TokenizeError::ConfigError("sites is not a mapping".to_string()))? {
            let site_id = site_id.as_str().ok_or_else(|| TokenizeError::ConfigError("site_id is not a string".to_string()))?;
            let entry: ConfigEntry = serde_yaml::from_value(value.clone())
                .map_err(|e| TokenizeError::ConfigError(format!("設定のパースに失敗: {}", e)))?;

            if let Some(aliases) = entry.aliases {
                for alias in aliases {
                    site_resolver.register_alias(site_id, &alias);
                }
            }
            site_resolver.register_alias(site_id, site_id);
        }
    }

    // 言語のエイリアス
    if let Some(languages) = CONFIG.get("languages") {
        for (lang_id, value) in languages.as_mapping().ok_or_else(|| TokenizeError::ConfigError("languages is not a mapping".to_string()))? {
            let lang_id = lang_id.as_str().ok_or_else(|| TokenizeError::ConfigError("language_id is not a string".to_string()))?;
            let entry: ConfigEntry = serde_yaml::from_value(value.clone())
                .map_err(|e| TokenizeError::ConfigError(format!("設定のパースに失敗: {}", e)))?;

            if let Some(aliases) = entry.aliases {
                for alias in aliases {
                    language_resolver.register_alias(lang_id, &alias);
                }
            }
            language_resolver.register_alias(lang_id, lang_id);
        }
    }

    Ok((command_resolver, site_resolver, language_resolver))
}

// 名前解決器のキャッシュ
static RESOLVERS: Lazy<Result<(NameResolver, NameResolver, NameResolver)>> = Lazy::new(build_resolvers);

impl CommandToken {
    /// コマンド文字列をパースしてコマンド種別とパラメータを抽出
    pub fn parse(input: &str) -> Result<Self> {
        let args: Vec<&str> = input.split_whitespace().collect();
        if args.is_empty() {
            return Err(TokenizeError::InvalidFormat("空のコマンドです".to_string()));
        }

        // 名前解決器の取得
        let (command_resolver, site_resolver, _) = RESOLVERS.as_ref()
            .map_err(|e| TokenizeError::ConfigError(format!("名前解決器の初期化に失敗: {}", e)))?;

        // コマンド候補の収集
        let mut command_candidates = Vec::new();
        for arg in &args {
            if let Some(cmd_type) = command_resolver.resolve(arg) {
                command_candidates.push((*arg, cmd_type));
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
                    if let Some(params) = try_match_ordered(&args, cmd_arg, ordered_pattern, &site_resolver) {
                        results.push((cmd_type.clone(), params));
                    }
                }
            }

            // 順序不定パターンをチェック
            if let Some(unordered_patterns) = &pattern.unordered {
                for unordered_pattern in unordered_patterns {
                    if let Some(params) = try_match_unordered(&args, cmd_arg, unordered_pattern, &site_resolver) {
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
    site_resolver: &NameResolver,
) -> Option<HashMap<String, String>> {
    let mut params = HashMap::new();
    let mut pattern_idx = 0;
    let mut arg_idx = 0;

    while arg_idx < args.len() && pattern_idx < pattern.len() {
        let arg = args[arg_idx];
        let param_type = &pattern[pattern_idx];

        if arg == cmd_arg {
            arg_idx += 1;
            continue;
        }

        match param_type.as_str() {
            "site_id" => {
                if let Some(site) = site_resolver.resolve(arg) {
                    params.insert("site_id".to_string(), site);
                    pattern_idx += 1;
                }
            }
            "problem_id" => {
                params.insert("problem_id".to_string(), arg.to_string());
                pattern_idx += 1;
            }
            "contest_id" => {
                params.insert("contest_id".to_string(), arg.to_string());
                pattern_idx += 1;
            }
            _ => return None,
        }
        arg_idx += 1;
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
    site_resolver: &NameResolver,
) -> Option<HashMap<String, String>> {
    let mut params = HashMap::new();
    let mut used_args = vec![false; args.len()];
    let mut matched_params = 0;

    // コマンド引数をマークする
    for (i, arg) in args.iter().enumerate() {
        if *arg == cmd_arg {
            used_args[i] = true;
            break;
        }
    }

    // 各パラメータタイプに対して、マッチする引数を探す
    for param_type in pattern {
        let mut found = false;
        for (i, &arg) in args.iter().enumerate() {
            if used_args[i] {
                continue;
            }

            match param_type.as_str() {
                "site_id" => {
                    if let Some(site) = site_resolver.resolve(arg) {
                        params.insert("site_id".to_string(), site);
                        used_args[i] = true;
                        found = true;
                        matched_params += 1;
                        break;
                    }
                }
                "problem_id" => {
                    params.insert("problem_id".to_string(), arg.to_string());
                    used_args[i] = true;
                    found = true;
                    matched_params += 1;
                    break;
                }
                "contest_id" => {
                    params.insert("contest_id".to_string(), arg.to_string());
                    used_args[i] = true;
                    found = true;
                    matched_params += 1;
                    break;
                }
                _ => return None,
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
        let (command_resolver, site_resolver, language_resolver) = RESOLVERS.as_ref().unwrap();

        // コマンドの解決
        assert!(command_resolver.aliases.contains_key("test"));
        assert!(command_resolver.aliases.contains_key("t"));
        assert!(command_resolver.aliases.contains_key("check"));

        // サイトの解決
        assert!(site_resolver.aliases.contains_key("atcoder"));
        assert!(site_resolver.aliases.contains_key("ac"));

        // 言語の解決
        assert!(language_resolver.aliases.contains_key("rust"));
        assert!(language_resolver.aliases.contains_key("rs"));
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