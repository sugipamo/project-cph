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

#[derive(Debug, Clone, Copy, PartialEq)]
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

    fn from_index(index: usize) -> Self {
        Self::all()[index]
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

    fn find_matches(&self, input: &str) -> Vec<String> {
        let mut matches = Vec::new();
        if let Some(name) = self.resolve(input) {
            matches.push(name);
        }
        matches
    }
}

#[derive(Debug, Clone)]
struct NameResolvers {
    resolvers: Vec<NameResolver>,
}

impl NameResolvers {
    fn new(resolvers: Vec<NameResolver>) -> Self {
        Self { resolvers }
    }

    fn find_matches(&self, input: &str) -> Vec<(ParamType, String)> {
        let mut matches = Vec::new();
        for (i, resolver) in self.resolvers.iter().enumerate() {
            for name in resolver.find_matches(input) {
                matches.push((ParamType::from_index(i), name));
            }
        }
        matches
    }

    fn get(&self, param_type: ParamType) -> &NameResolver {
        &self.resolvers[param_type as usize]
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
static RESOLVERS: Lazy<Result<NameResolvers>> = Lazy::new(|| {
    build_resolvers().map(NameResolvers::new)
});

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
            let matches = resolvers.find_matches(arg);
            for (param_type, cmd_type) in matches {
                if param_type == ParamType::Command {
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
            let mut current_matches = Vec::new();
            
            // 順序固定パターンをチェック
            if let Some(ordered_patterns) = &pattern.ordered {
                for ordered_pattern in ordered_patterns {
                    if let Some(params) = try_match_ordered(&args, cmd_arg, ordered_pattern, &resolvers.resolvers) {
                        current_matches.push((ordered_pattern.len(), true, cmd_type.clone(), params));
                    }
                }
            }

            // 順序不定パターンをチェック
            if let Some(unordered_patterns) = &pattern.unordered {
                for unordered_pattern in unordered_patterns {
                    if let Some(params) = try_match_unordered(&args, cmd_arg, unordered_pattern, &resolvers.resolvers) {
                        current_matches.push((unordered_pattern.len(), false, cmd_type.clone(), params));
                    }
                }
            }

            // 最も長いパターンを見つける
            if let Some(max_len) = current_matches.iter().map(|(len, _, _, _)| *len).max() {
                // 最長のパターンの中から、orderedを優先して選択
                let best_match = current_matches.iter()
                    .filter(|(len, _, _, _)| *len == max_len)
                    .max_by_key(|(_, is_ordered, _, _)| *is_ordered);
                
                if let Some((_, _, cmd, params)) = best_match {
                    results.push((cmd.clone(), params.clone()));
                }
            }
        }

        // 結果の重複を除去
        let mut unique_results = Vec::new();
        for result in results {
            if !unique_results.contains(&result) {
                unique_results.push(result);
            }
        }

        match unique_results.len() {
            0 => Err(TokenizeError::NoMatch),
            1 => {
                let (command_type, parameters) = unique_results.into_iter().next().unwrap();
                Ok(CommandToken {
                    command_name: command_type,
                    arguments: parameters,
                })
            }
            _ => {
                let candidates: Vec<String> = unique_results
                    .into_iter()
                    .map(|(cmd_type, _)| cmd_type)
                    .collect();
                Err(TokenizeError::MultipleMatches(candidates))
            }
        }
    }
}

fn try_match_ordered(
    _args: &[&str],
    _cmd_arg: &str,
    _pattern: &[String],
    _resolvers: &[NameResolver],
) -> Option<HashMap<String, String>> {
    None
}

fn try_match_unordered(
    _args: &[&str],
    _cmd_arg: &str,
    _pattern: &[String],
    _resolvers: &[NameResolver],
) -> Option<HashMap<String, String>> {
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    // NameResolversのテスト用のヘルパー関数
    fn create_test_resolvers() -> NameResolvers {
        let mut command_resolver = NameResolver::new();
        command_resolver.register_alias("test", "test");
        command_resolver.register_alias("test", "t");
        command_resolver.register_alias("test", "check");

        let mut site_resolver = NameResolver::new();
        site_resolver.register_alias("atcoder", "atcoder");
        site_resolver.register_alias("atcoder", "ac");
        site_resolver.register_alias("codeforces", "codeforces");
        site_resolver.register_alias("codeforces", "cf");

        let mut language_resolver = NameResolver::new();
        language_resolver.register_alias("rust", "rust");
        language_resolver.register_alias("rust", "rs");
        language_resolver.register_alias("python", "python");
        language_resolver.register_alias("python", "py");

        NameResolvers::new(vec![command_resolver, site_resolver, language_resolver])
    }

    #[test]
    fn test_name_resolvers_basic() {
        let resolvers = create_test_resolvers();

        // コマンドの解決
        let matches = resolvers.find_matches("test");
        assert_eq!(matches, vec![(ParamType::Command, "test".to_string())]);

        // サイトの解決
        let matches = resolvers.find_matches("atcoder");
        assert_eq!(matches, vec![(ParamType::Site, "atcoder".to_string())]);

        // 言語の解決
        let matches = resolvers.find_matches("rust");
        assert_eq!(matches, vec![(ParamType::Language, "rust".to_string())]);
    }

    #[test]
    fn test_name_resolvers_aliases() {
        let resolvers = create_test_resolvers();

        // コマンドのエイリアス
        let matches = resolvers.find_matches("t");
        assert_eq!(matches, vec![(ParamType::Command, "test".to_string())]);

        // サイトのエイリアス
        let matches = resolvers.find_matches("ac");
        assert_eq!(matches, vec![(ParamType::Site, "atcoder".to_string())]);

        // 言語のエイリアス
        let matches = resolvers.find_matches("rs");
        assert_eq!(matches, vec![(ParamType::Language, "rust".to_string())]);
    }

    #[test]
    fn test_name_resolvers_no_match() {
        let resolvers = create_test_resolvers();

        // 存在しない入力
        let matches = resolvers.find_matches("nonexistent");
        assert!(matches.is_empty());

        // 空文字列
        let matches = resolvers.find_matches("");
        assert!(matches.is_empty());
    }

    #[test]
    fn test_name_resolvers_multiple_matches() {
        let mut resolvers = create_test_resolvers();
        
        // 意図的に複数のリゾルバに同じエイリアスを登録
        resolvers.resolvers[ParamType::Command as usize].register_alias("common", "x");
        resolvers.resolvers[ParamType::Site as usize].register_alias("common", "x");
        resolvers.resolvers[ParamType::Language as usize].register_alias("common", "x");

        let matches = resolvers.find_matches("x");
        assert_eq!(matches.len(), 3);
        assert!(matches.contains(&(ParamType::Command, "common".to_string())));
        assert!(matches.contains(&(ParamType::Site, "common".to_string())));
        assert!(matches.contains(&(ParamType::Language, "common".to_string())));
    }

    #[test]
    fn test_name_resolvers_get() {
        let resolvers = create_test_resolvers();

        // 各パラメータタイプのリゾルバを取得して正しく動作することを確認
        let command_resolver = resolvers.get(ParamType::Command);
        assert_eq!(command_resolver.resolve("test"), Some("test".to_string()));
        assert_eq!(command_resolver.resolve("t"), Some("test".to_string()));

        let site_resolver = resolvers.get(ParamType::Site);
        assert_eq!(site_resolver.resolve("atcoder"), Some("atcoder".to_string()));
        assert_eq!(site_resolver.resolve("ac"), Some("atcoder".to_string()));

        let language_resolver = resolvers.get(ParamType::Language);
        assert_eq!(language_resolver.resolve("rust"), Some("rust".to_string()));
        assert_eq!(language_resolver.resolve("rs"), Some("rust".to_string()));
    }

    #[test]
    #[ignore]
    fn test_resolver_initialization() {
        let resolvers = RESOLVERS.as_ref().unwrap();
        let command_resolver = resolvers.get(ParamType::Command);
        let site_resolver = resolvers.get(ParamType::Site);
        let language_resolver = resolvers.get(ParamType::Language);

        // コマンドの解決
        assert!(command_resolver.resolve("test").is_some());
        assert!(command_resolver.resolve("t").is_some());
        assert!(command_resolver.resolve("check").is_some());

        // サイトの解決
        assert!(site_resolver.resolve("atcoder").is_some());
        assert!(site_resolver.resolve("ac").is_some());

        // 言語の解決
        assert!(language_resolver.resolve("rust").is_some());
        assert!(language_resolver.resolve("rs").is_some());
    }

    #[test]
    #[ignore]
    fn test_basic_command() {
        let input = "test abc123";
        let result = CommandToken::parse(input).unwrap();
        assert_eq!(result.command_name, "test");
        assert_eq!(result.arguments["problem_id"], "abc123");
    }

    #[test]
    #[ignore]
    fn test_command_with_underscore() {
        let input = "test abc_123";
        let result = CommandToken::parse(input).unwrap();
        assert_eq!(result.command_name, "test");
        assert_eq!(result.arguments["problem_id"], "abc_123");
    }

    #[test]
    #[ignore]
    fn test_command_with_site() {
        let input = "atcoder test abc123";
        let result = CommandToken::parse(input).unwrap();
        assert_eq!(result.command_name, "test");
        assert_eq!(result.arguments["site_id"], "atcoder");
        assert_eq!(result.arguments["problem_id"], "abc123");
    }

    #[test]
    #[ignore]
    fn test_command_with_contest() {
        let input = "test abc123 d";
        let result = CommandToken::parse(input).unwrap();
        assert_eq!(result.command_name, "test");
        assert_eq!(result.arguments["contest_id"], "abc123");
        assert_eq!(result.arguments["problem_id"], "d");
    }

    #[test]
    #[ignore]
    fn test_command_aliases() {
        for cmd in ["test", "t", "check"] {
            let input = format!("{} abc123", cmd);
            let result = CommandToken::parse(&input).unwrap();
            assert_eq!(result.command_name, "test");
            assert_eq!(result.arguments["problem_id"], "abc123");
        }
    }

    #[test]
    #[ignore]
    fn test_multiple_matches() {
        let inputs = &[
            "test atcoder d",  // atcoderがsite_idかproblem_idか曖昧
            "test abc d",      // abcがcontest_id + problem_idか、problem_idか曖昧
        ];

        for input in inputs {
            match CommandToken::parse(input) {
                Err(TokenizeError::MultipleMatches(candidates)) => {
                    assert!(candidates.len() > 1);
                }
                Ok(token) => {
                    panic!("入力 '{}' に対して複数マッチエラーが発生するべきですが、1つのパターンにマッチしました: command={}, args={:?}", 
                        input, token.command_name, token.arguments);
                }
                Err(e) => {
                    panic!("入力 '{}' に対して複数マッチエラーが発生するべきですが、異なるエラーが発生しました: {}", input, e);
                }
            }
        }
    }

    #[test]
    #[ignore]
    fn test_invalid_command() {
        let input = "invalid xyz";
        assert!(matches!(CommandToken::parse(input), Err(TokenizeError::NoMatch)));
    }

    #[test]
    #[ignore]
    fn test_empty_command() {
        let input = "";
        assert!(matches!(
            CommandToken::parse(input),
            Err(TokenizeError::InvalidFormat(_))
        ));
    }

    #[test]
    #[ignore]
    fn test_command_with_extra_spaces() {
        let input = "  test   abc123  ";
        let result = CommandToken::parse(input).unwrap();
        assert_eq!(result.command_name, "test");
        assert_eq!(result.arguments["problem_id"], "abc123");
    }

    #[test]
    #[ignore]
    fn test_command_case_sensitivity() {
        let input = "TEST abc123";
        assert!(matches!(CommandToken::parse(input), Err(TokenizeError::NoMatch)));
    }

    #[test]
    #[ignore]
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
    #[ignore]
    fn test_command_with_all_parameters() {
        let input = "atcoder test abc123";
        let result = CommandToken::parse(input).unwrap();
        assert_eq!(result.command_name, "test");
        assert_eq!(result.arguments["site_id"], "atcoder");
        assert_eq!(result.arguments["problem_id"], "abc123");
    }

    #[test]
    #[ignore]
    fn test_command_with_site_alias() {
        let input = "ac test abc123";
        let result = CommandToken::parse(input).unwrap();
        assert_eq!(result.command_name, "test");
        assert_eq!(result.arguments["site_id"], "atcoder");
        assert_eq!(result.arguments["problem_id"], "abc123");
    }
} 