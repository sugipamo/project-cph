use std::collections::HashMap;
use serde::Deserialize;
use once_cell::sync::Lazy;

#[allow(dead_code)]
#[derive(Debug, Clone, Deserialize)]
pub struct ParameterType {
    pub name: String,
    pub pattern: String,
    #[serde(default)]
    pub config_key: Option<String>,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Deserialize)]
pub struct CommandConfig {
    pub parameter_types: Vec<ParameterType>,
    pub commands: HashMap<String, CommandPattern>,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Deserialize)]
pub struct CommandPattern {
    pub commands: Vec<String>,
    pub ordered: Option<Vec<Vec<String>>>,
    pub unordered: Option<Vec<Vec<String>>>,
}

// 設定ファイルの読み込み
#[allow(dead_code)]
static COMMAND_CONFIG: Lazy<serde_yaml::Value> = Lazy::new(|| {
    let config_str = include_str!("commands.yaml");
    serde_yaml::from_str(config_str).expect("コマンド設定の読み込みに失敗")
});

#[allow(dead_code)]
#[derive(Debug, Clone)]
pub struct NameResolver {
    param_type: String,
    aliases: HashMap<String, String>,
}

impl NameResolver {
    fn new(param_type: String) -> Self {
        Self {
            param_type,
            aliases: HashMap::new(),
        }
    }

    pub fn register_alias(&mut self, name: &str, alias: &str) {
        self.aliases.insert(alias.to_string(), name.to_string());
    }

    pub fn resolve(&self, input: &str) -> Option<String> {
        self.aliases.get(input).cloned()
    }
}

#[allow(dead_code)]
#[derive(Debug, Clone)]
pub struct NameResolvers {
    resolvers: Vec<NameResolver>,
}

impl NameResolvers {
    pub fn new() -> Self {
        Self::new_with_config(&COMMAND_CONFIG)
    }

    fn new_with_config(command_config: &serde_yaml::Value) -> Self {
        let mut resolvers = Vec::new();
        let mut resolver_map = HashMap::new();

        // parameter_typesからリゾルバの型を取得
        if let Some(parameter_types) = command_config.get("parameter_types") {
            if let Some(parameter_types) = parameter_types.as_sequence() {
                for param_type in parameter_types {
                    if let Some(name) = param_type.get("name").and_then(|n| n.as_str()) {
                        if cfg!(test) { println!("リゾルバ型を登録: {}", name); }
                        resolver_map.insert(
                            param_type.get("pattern").and_then(|p| p.as_str()).unwrap_or(name),
                            name.to_string()
                        );
                    }
                }
            }
        }

        // 設定ファイルから各セクションのエイリアスを読み込む
        for cfg in [command_config].iter() {
            let Some(map) = cfg.as_mapping() else { 
                if cfg!(test) { println!("設定がマッピングではありません"); }
                continue;
            };

            // 各セクション（commands, sites, languages等）を処理
            for (section_name, section_value) in map {
                let Some(section_name) = section_name.as_str() else { 
                    if cfg!(test) { println!("セクション名が文字列ではありません"); }
                    continue;
                };
                if cfg!(test) { println!("セクション処理: {}", section_name); }

                let Some(section) = section_value.as_mapping() else { 
                    if cfg!(test) { println!("セクション値がマッピングではありません: {}", section_name); }
                    continue;
                };

                // セクション内の各要素を処理
                let mut resolver = None;
                for (name, item) in section {
                    let Some(name) = name.as_str() else { 
                        if cfg!(test) { println!("要素名が文字列ではありません"); }
                        continue;
                    };
                    if name.starts_with('_') { 
                        if cfg!(test) { println!("アンダースコアで始まる要素をスキップ: {}", name); }
                        continue;
                    };

                    // エイリアスの取得
                    let Some(aliases) = item.get("aliases") else { 
                        if cfg!(test) { println!("エイリアスが見つかりません: {}.{}", section_name, name); }
                        continue;
                    };
                    let Some(aliases) = aliases.as_sequence() else { 
                        if cfg!(test) { println!("エイリアスが配列ではありません: {}.{}", section_name, name); }
                        continue;
                    };

                    // リゾルバの初期化（最初のエイリアスが見つかった時）
                    if resolver.is_none() {
                        if let Some(resolver_type) = resolver_map.get(section_name) {
                            if cfg!(test) { println!("リゾルバを作成: {}", resolver_type); }
                            resolver = Some(NameResolver::new(resolver_type.clone()));
                        } else {
                            if cfg!(test) { println!("リゾルバ型が見つかりません: {}", section_name); }
                            continue;
                        }
                    }

                    // エイリアスの登録
                    if let Some(resolver) = resolver.as_mut() {
                        // 元の名前自体もエイリアスとして登録
                        resolver.register_alias(name, name);
                        if cfg!(test) { println!("エイリアスを登録: {} -> {}", name, name); }

                        // 設定ファイルに定義されたエイリアスを登録
                        for alias in aliases {
                            if let Some(alias) = alias.as_str() {
                                resolver.register_alias(name, alias);
                                if cfg!(test) { println!("エイリアスを登録: {} -> {}", alias, name); }
                            }
                        }
                    }
                }

                // エイリアスが見つかったセクションのみリゾルバを追加
                if let Some(resolver) = resolver {
                    if cfg!(test) { println!("リゾルバを追加: {}", resolver.param_type); }
                    resolvers.push(resolver);
                }
            }
        }

        Self { resolvers }
    }

    pub fn get(&self, index: usize) -> Option<&NameResolver> {
        self.resolvers.get(index)
    }

    pub fn find_matches(&self, input: &str) -> Vec<(usize, String)> {
        let mut matches = Vec::new();
        for (index, resolver) in self.resolvers.iter().enumerate() {
            if let Some(name) = resolver.resolve(input) {
                matches.push((index, name));
            }
        }
        matches
    }

    fn find_matches_for_arg(&self, arg: &str) -> Vec<(String, String)> {
        if cfg!(test) {
            println!("引数のマッチを試行: {}", arg);
        }
        // 全てのリゾルバでマッチを試行し、マッチしたものを全て返す
        let mut matches = Vec::new();
        for resolver in &self.resolvers {
            if cfg!(test) {
                println!("  リゾルバをチェック: {}", resolver.param_type);
            }
            // 設定ファイルに存在する型のみをマッチ対象とする
            if let Some(parameter_types) = COMMAND_CONFIG.get("parameter_types") {
                if let Some(parameter_types) = parameter_types.as_sequence() {
                    if parameter_types.iter().any(|pt| {
                        pt.get("name").and_then(|n| n.as_str()) == Some(&resolver.param_type)
                    }) {
                        if let Some(value) = resolver.resolve(arg) {
                            if cfg!(test) {
                                println!("  マッチ成功: {} -> {}", resolver.param_type, value);
                            }
                            matches.push((resolver.param_type.clone(), value));
                        }
                    }
                }
            }
        }
        if matches.is_empty() && cfg!(test) {
            println!("  マッチ失敗");
        }
        matches
    }

    fn normalize_input<'a>(&self, input: &'a str) -> Result<Vec<&'a str>, String> {
        let normalized: Vec<&'a str> = input.split_whitespace().collect();
        if normalized.is_empty() {
            return Err("空のコマンドです".to_string());
        }
        Ok(normalized)
    }

    fn check_pattern_matches(&self, pattern: &[String], matched_args: &[Vec<(String, String)>]) -> bool {
        // 長さが異なる場合は即座にfalse
        if pattern.len() != matched_args.len() {
            return false;
        }

        // 各パターン要素について、対応する位置の引数とマッチするか確認
        pattern.iter().enumerate().all(|(i, param_type)| {
            // マッチが空の場合は、まだ型が決定されていないので許容する
            if matched_args[i].is_empty() {
                return true;
            }
            // マッチが存在する場合は、少なくとも1つのマッチが期待される型と一致する必要がある
            matched_args[i].iter().any(|(arg_type, _)| arg_type == param_type)
        })
    }

    fn get_patterns(&self, pattern_type: fn(&CommandPattern) -> &Option<Vec<Vec<String>>>, args_len: usize) -> Vec<Vec<String>> {
        if let Some(commands) = COMMAND_CONFIG.get("commands") {
            if let Some(commands) = commands.as_mapping() {
                return commands.values()
                    .filter_map(|cmd| {
                        let cmd_pattern: CommandPattern = serde_yaml::from_value(cmd.clone()).ok()?;
                        pattern_type(&cmd_pattern).as_ref().map(|patterns| patterns.clone())
                    })
                    .flat_map(|patterns| patterns)
                    .filter(|pattern| pattern.len() == args_len)
                    .collect();
            }
        }
        Vec::new()
    }

    pub fn parse_command(&self, input: &str) -> Result<ParsedCommand, String> {
        let mut result = ParsedCommand::new();
        
        // 入力の正規化
        let normalized = self.normalize_input(input)?;
        if cfg!(test) {
            println!("正規化された入力: {:?}", normalized);
        }

        // 各引数に対してマッチを試行
        let matched_args: Vec<Vec<(String, String)>> = normalized.iter()
            .map(|&arg| self.find_matches_for_arg(arg))
            .collect();
        if cfg!(test) {
            println!("マッチした引数: {:?}", matched_args);
        }

        // コマンドパターンの候補を取得
        let args_len = normalized.len();

        // マッチするパターンを探す
        let ordered_patterns = self.get_patterns(|cmd| &cmd.ordered, args_len);
        if cfg!(test) {
            println!("取得した順序付きパターン: {:?}", ordered_patterns);
        }
        let matching_ordered: Vec<_> = ordered_patterns.iter()
            .filter(|pattern| self.check_pattern_matches(pattern, &matched_args))
            .collect();
        if cfg!(test) {
            println!("マッチした順序付きパターン: {:?}", matching_ordered);
        }

        let unordered_patterns = self.get_patterns(|cmd| &cmd.unordered, args_len);
        let matching_unordered: Vec<_> = unordered_patterns.iter()
            .filter(|pattern| self.check_pattern_matches(pattern, &matched_args))
            .collect();
        if cfg!(test) {
            println!("マッチした順序なしパターン: {:?}", matching_unordered);
        }

        // マッチしたパターンが存在しない場合はエラー
        if matching_ordered.is_empty() && matching_unordered.is_empty() {
            return Err("マッチするコマンドパターンが見つかりません".to_string());
        }

        // マッチしたパターンから結果を構築
        for (_i, matches) in matched_args.iter().enumerate() {
            if matches.is_empty() {
                continue;
            }

            // 最初にマッチした値を使用
            let (param_type, value) = &matches[0];
            match param_type.as_str() {
                "command" => result.command = Some(value.clone()),
                "site_id" => result.site_id = Some(value.clone()),
                "contest_id" => result.contest_id = Some(value.clone()),
                "problem_id" => result.problem_id = Some(value.clone()),
                "language" => result.language = Some(value.clone()),
                _ => {},
            }
        }

        Ok(result)
    }
}

#[derive(Debug, Default)]
pub struct ParsedCommand {
    pub command: Option<String>,
    pub site_id: Option<String>,
    pub contest_id: Option<String>,
    pub problem_id: Option<String>,
    pub language: Option<String>,
}

impl ParsedCommand {
    pub fn new() -> Self {
        Self::default()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    mod name_resolver {
        use super::*;

        #[test]
        fn test_resolver_basic() {
            let mut resolver = NameResolver::new("test_type".to_string());
            
            // 基本的なエイリアス登録と解決
            resolver.register_alias("original", "alias");
            assert_eq!(resolver.resolve("alias"), Some("original".to_string()));
            
            // 元の名前でも解決できることを確認
            assert_eq!(resolver.resolve("original"), Some("original".to_string()));
            
            // 存在しない名前の解決
            assert_eq!(resolver.resolve("unknown"), None);
        }

        #[test]
        fn test_resolver_multiple_aliases() {
            let mut resolver = NameResolver::new("test_type".to_string());
            
            // 複数のエイリアスを登録
            resolver.register_alias("original", "alias1");
            resolver.register_alias("original", "alias2");
            
            // 全てのエイリアスが解決できることを確認
            assert_eq!(resolver.resolve("alias1"), Some("original".to_string()));
            assert_eq!(resolver.resolve("alias2"), Some("original".to_string()));
            assert_eq!(resolver.resolve("original"), Some("original".to_string()));
        }
    }

    mod name_resolvers {
        use super::*;

        fn create_test_resolvers() -> NameResolvers {
            let mut command_resolver = NameResolver::new("command".to_string());
            command_resolver.register_alias("test", "test");
            command_resolver.register_alias("test", "t");
            command_resolver.register_alias("submit", "submit");
            command_resolver.register_alias("submit", "s");
            command_resolver.register_alias("language", "language");
            command_resolver.register_alias("language", "l");

            let mut site_resolver = NameResolver::new("site_id".to_string());
            site_resolver.register_alias("atcoder", "atcoder");
            site_resolver.register_alias("atcoder", "ac");

            let mut language_resolver = NameResolver::new("language".to_string());
            language_resolver.register_alias("rust", "rust");
            language_resolver.register_alias("rust", "rs");
            language_resolver.register_alias("python", "python");
            language_resolver.register_alias("python", "py");

            NameResolvers {
                resolvers: vec![command_resolver, site_resolver, language_resolver],
            }
        }

        #[test]
        fn test_resolvers_basic() {
            let resolvers = create_test_resolvers();
            
            // コマンド型のリゾルバが存在することを確認
            let command_resolver = resolvers.get(0).expect("コマンドリゾルバが存在しない");
            assert_eq!(command_resolver.resolve("test"), Some("test".to_string()));
            assert_eq!(command_resolver.resolve("t"), Some("test".to_string()));

            // サイト型のリゾルバが存在することを確認
            let site_resolver = resolvers.get(1).expect("サイトリゾルバが存在しない");
            assert_eq!(site_resolver.resolve("atcoder"), Some("atcoder".to_string()));
            assert_eq!(site_resolver.resolve("ac"), Some("atcoder".to_string()));
        }

        #[test]
        fn test_find_matches() {
            let resolvers = create_test_resolvers();
            
            // コマンドのマッチを確認
            let matches = resolvers.find_matches("test");
            assert_eq!(matches.len(), 1);
            assert_eq!(matches[0], (0, "test".to_string()));

            // エイリアスのマッチを確認
            let matches = resolvers.find_matches("ac");
            assert_eq!(matches.len(), 1);
            assert_eq!(matches[0], (1, "atcoder".to_string()));

            // 存在しない値のマッチを確認
            let matches = resolvers.find_matches("unknown");
            assert_eq!(matches.len(), 0);
        }

        #[test]
        fn test_find_matches_for_arg() {
            let resolvers = create_test_resolvers();
            
            // コマンドのマッチを確認
            let matches = resolvers.find_matches_for_arg("test");
            assert_eq!(matches.len(), 1);
            assert_eq!(matches[0], ("command".to_string(), "test".to_string()));

            // エイリアスのマッチを確認
            let matches = resolvers.find_matches_for_arg("ac");
            assert_eq!(matches.len(), 1);
            assert_eq!(matches[0], ("site_id".to_string(), "atcoder".to_string()));

            // 存在しない値のマッチを確認
            let matches = resolvers.find_matches_for_arg("unknown");
            assert_eq!(matches.len(), 0);

            // 複数のリゾルバにマッチする場合
            let mut resolver = create_test_resolvers();
            let mut another_resolver = NameResolver::new("another".to_string());
            another_resolver.register_alias("test", "test");
            resolver.resolvers.push(another_resolver);

            let matches = resolver.find_matches_for_arg("test");
            assert_eq!(matches.len(), 2);
            assert!(matches.contains(&("command".to_string(), "test".to_string())));
            assert!(matches.contains(&("another".to_string(), "test".to_string())));
        }

        #[test]
        fn test_normalize_input() {
            let resolvers = create_test_resolvers();
            
            // 基本的な入力の正規化
            let result = resolvers.normalize_input("test abc001 a");
            assert!(result.is_ok());
            let normalized = result.unwrap();
            assert_eq!(normalized, vec!["test", "abc001", "a"]);

            // 複数のスペースを含む入力
            let result = resolvers.normalize_input("test   abc001    a");
            assert!(result.is_ok());
            let normalized = result.unwrap();
            assert_eq!(normalized, vec!["test", "abc001", "a"]);

            // 前後のスペースを含む入力
            let result = resolvers.normalize_input("  test abc001 a  ");
            assert!(result.is_ok());
            let normalized = result.unwrap();
            assert_eq!(normalized, vec!["test", "abc001", "a"]);

            // 空の入力
            let result = resolvers.normalize_input("");
            assert!(result.is_err());
            assert_eq!(result.unwrap_err(), "空のコマンドです".to_string());

            // スペースのみの入力
            let result = resolvers.normalize_input("   ");
            assert!(result.is_err());
            assert_eq!(result.unwrap_err(), "空のコマンドです".to_string());
        }

        #[test]
        fn test_check_pattern_matches() {
            let resolvers = create_test_resolvers();
            
            // パターンと引数の準備
            let pattern = vec![
                "command".to_string(),
                "site_id".to_string(),
            ];

            // 完全一致のケース
            let matched_args = vec![
                vec![("command".to_string(), "test".to_string())],
                vec![("site_id".to_string(), "atcoder".to_string())],
            ];
            assert!(resolvers.check_pattern_matches(&pattern, &matched_args));

            // 順序が一致しないケース
            let matched_args = vec![
                vec![("site_id".to_string(), "atcoder".to_string())],
                vec![("command".to_string(), "test".to_string())],
            ];
            assert!(!resolvers.check_pattern_matches(&pattern, &matched_args));

            // 長さが異なるケース
            let matched_args = vec![
                vec![("command".to_string(), "test".to_string())],
            ];
            assert!(!resolvers.check_pattern_matches(&pattern, &matched_args));

            // 空のマッチを含むケース（型が未決定の場合）
            let matched_args = vec![
                vec![("command".to_string(), "test".to_string())],
                vec![],
            ];
            assert!(resolvers.check_pattern_matches(&pattern, &matched_args));

            // 複数のマッチを含むケース
            let matched_args = vec![
                vec![
                    ("command".to_string(), "test".to_string()),
                    ("another".to_string(), "test".to_string()),
                ],
                vec![("site_id".to_string(), "atcoder".to_string())],
            ];
            assert!(resolvers.check_pattern_matches(&pattern, &matched_args));
        }

        #[test]
        fn test_get_patterns() {
            let resolvers = create_test_resolvers();
            
            // 順序付きパターンのテスト
            let ordered_patterns = resolvers.get_patterns(|cmd| &cmd.ordered, 2);
            assert!(!ordered_patterns.is_empty());
            
            // 順序なしパターンのテスト
            let unordered_patterns = resolvers.get_patterns(|cmd| &cmd.unordered, 3);
            assert!(!unordered_patterns.is_empty());

            // 存在しない長さのパターン
            let patterns = resolvers.get_patterns(|cmd| &cmd.ordered, 10);
            assert!(patterns.is_empty());

            // パターンの内容確認
            let patterns = resolvers.get_patterns(|cmd| &cmd.ordered, 2);
            assert!(patterns.iter().any(|p| {
                p.len() == 2 && p[0] == "command" && p[1] == "problem_id"
            }));
        }

        #[test]
        fn test_parse_command() {
            let resolvers = create_test_resolvers();
            
            // 基本的なコマンドのパース
            let result = resolvers.parse_command("test abc001 a");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.command, Some("test".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));

            // エイリアスを含むコマンドのパース
            let result = resolvers.parse_command("t abc001 a");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.command, Some("test".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));

            // サイトIDを含むコマンドのパース
            let result = resolvers.parse_command("ac test abc001 a");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.site_id, Some("atcoder".to_string()));
            assert_eq!(parsed.command, Some("test".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));

            // 順序なしパターンのパース
            let result = resolvers.parse_command("abc001 a test");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.command, Some("test".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));

            // 全てエイリアスを使用したパース
            let result = resolvers.parse_command("ac t abc001 a");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.site_id, Some("atcoder".to_string()));
            assert_eq!(parsed.command, Some("test".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));

            // 余分なスペースを含むパース
            let result = resolvers.parse_command("  ac   test   abc001   a  ");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.site_id, Some("atcoder".to_string()));
            assert_eq!(parsed.command, Some("test".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));

            // エラーケース
            // 空のコマンド
            let result = resolvers.parse_command("");
            assert!(result.is_err());

            // スペースのみのコマンド
            let result = resolvers.parse_command("   ");
            assert!(result.is_err());

            // 未知のコマンド
            let result = resolvers.parse_command("unknown abc001 a");
            assert!(result.is_err());

            // パラメータ不足
            let result = resolvers.parse_command("test");
            assert!(result.is_err());

            // パラメータ過剰
            let result = resolvers.parse_command("test abc001 a extra param");
            assert!(result.is_err());

            // 未知のエイリアス
            let result = resolvers.parse_command("unknown_site test abc001 a");
            assert!(result.is_err());
        }

        #[test]
        fn test_parse_command_with_language() {
            let resolvers = create_test_resolvers();
            
            // 基本的な言語指定付きテストコマンド
            let result = resolvers.parse_command("test abc001 a rust");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.command, Some("test".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));
            assert_eq!(parsed.language, Some("rust".to_string()));

            // エイリアスを使用した言語指定
            let result = resolvers.parse_command("t abc001 a rs");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.command, Some("test".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));
            assert_eq!(parsed.language, Some("rust".to_string()));

            // サイトIDと言語指定を含むテストコマンド
            let result = resolvers.parse_command("ac test abc001 a python");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.site_id, Some("atcoder".to_string()));
            assert_eq!(parsed.command, Some("test".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));
            assert_eq!(parsed.language, Some("python".to_string()));

            // 順序なしパターンでの言語指定
            let result = resolvers.parse_command("abc001 a test py");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.command, Some("test".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));
            assert_eq!(parsed.language, Some("python".to_string()));

            // 不正な言語指定
            let result = resolvers.parse_command("test abc001 a invalid_lang");
            assert!(result.is_err());
        }

        #[test]
        fn test_parse_submit_with_language() {
            let resolvers = create_test_resolvers();
            
            // 基本的な言語指定付き提出コマンド
            let result = resolvers.parse_command("submit abc001 a rust");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.command, Some("submit".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));
            assert_eq!(parsed.language, Some("rust".to_string()));

            // エイリアスを使用した言語指定
            let result = resolvers.parse_command("s abc001 a rs");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.command, Some("submit".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));
            assert_eq!(parsed.language, Some("rust".to_string()));

            // サイトIDと言語指定を含む提出コマンド
            let result = resolvers.parse_command("ac submit abc001 a python");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.site_id, Some("atcoder".to_string()));
            assert_eq!(parsed.command, Some("submit".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));
            assert_eq!(parsed.language, Some("python".to_string()));

            // 順序なしパターンでの言語指定
            let result = resolvers.parse_command("abc001 a submit py");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.command, Some("submit".to_string()));
            assert_eq!(parsed.contest_id, Some("abc001".to_string()));
            assert_eq!(parsed.problem_id, Some("a".to_string()));
            assert_eq!(parsed.language, Some("python".to_string()));

            // 不正な言語指定
            let result = resolvers.parse_command("submit abc001 a invalid_lang");
            assert!(result.is_err());
        }

        #[test]
        fn test_parse_ambiguous_commands() {
            let resolvers = create_test_resolvers();
            
            // test submitのケース
            let result = resolvers.parse_command("test submit abc001 a");
            assert!(result.is_err());
            assert!(result.unwrap_err().contains("マッチするコマンドパターンが見つかりません"));

            // submitをproblem_idとして解釈するケース
            let result = resolvers.parse_command("test submit");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.command, Some("test".to_string()));
            assert_eq!(parsed.problem_id, Some("submit".to_string()));

            // test submit with language
            let result = resolvers.parse_command("test submit rust");
            assert!(result.is_ok());
            let parsed = result.unwrap();
            assert_eq!(parsed.command, Some("test".to_string()));
            assert_eq!(parsed.problem_id, Some("submit".to_string()));
            assert_eq!(parsed.language, Some("rust".to_string()));
        }
    }
}
