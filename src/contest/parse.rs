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
static COMMAND_CONFIG: Lazy<CommandConfig> = Lazy::new(|| {
    let config_str = include_str!("../../src/config/commands.yaml");
    serde_yaml::from_str(config_str).expect("コマンド設定の読み込みに失敗")
});

#[allow(dead_code)]
static CONFIG: Lazy<serde_yaml::Value> = Lazy::new(|| {
    let config_str = include_str!("../../src/config/config.yaml");
    serde_yaml::from_str(config_str).expect("設定ファイルの読み込みに失敗")
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

    fn load_aliases_from_config(&mut self, config: &serde_yaml::Value) {
        if cfg!(test) && std::env::var("TEST_DEBUG").is_ok() {
            println!("Loading aliases for type: {}", self.param_type);
        }

        // コマンドのエイリアスはcommands.yamlから読み込む
        if self.param_type == "command" {
            if cfg!(test) && std::env::var("TEST_DEBUG").is_ok() {
                println!("Loading command aliases from COMMAND_CONFIG");
            }
            for (name, pattern) in &COMMAND_CONFIG.commands {
                for alias in &pattern.commands {
                    if cfg!(test) && std::env::var("TEST_DEBUG").is_ok() {
                        println!("Registering command alias: {} -> {}", alias, name);
                    }
                    self.register_alias(name, alias);
                }
            }
            return;
        }

        // config.yamlから該当する型のエイリアスのみを読み込む
        let config_key = COMMAND_CONFIG.parameter_types.iter()
            .find(|pt| pt.name == self.param_type)
            .and_then(|pt| pt.config_key.as_ref())
            .map(|s| s.as_str());

        if let Some(key) = config_key {
            if let Some(section) = config.get(key) {
                if let Some(items) = section.as_mapping() {
                    for (name, item_value) in items {
                        if let Some(name) = name.as_str() {
                            if !name.starts_with('_') {
                                // 元の名前自体をエイリアスとして登録
                                self.register_alias(name, name);

                                // エイリアスの登録
                                if let Some(aliases) = item_value.get("aliases") {
                                    if let Some(aliases) = aliases.as_sequence() {
                                        for alias in aliases {
                                            if let Some(alias) = alias.as_str() {
                                                self.register_alias(name, alias);
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

#[allow(dead_code)]
#[derive(Debug, Clone)]
pub struct NameResolvers {
    resolvers: Vec<NameResolver>,
}

impl NameResolvers {
    pub fn new() -> Self {
        let mut resolvers: Vec<NameResolver> = COMMAND_CONFIG.parameter_types
            .iter()
            .map(|pt| NameResolver::new(pt.name.clone()))
            .collect();

        // 各リゾルバにエイリアスを読み込む
        for resolver in &mut resolvers {
            resolver.load_aliases_from_config(&CONFIG);
        }

        Self { resolvers }
    }

    pub fn get(&self, index: usize) -> Option<&NameResolver> {
        self.resolvers.get(index)
    }

    pub fn get_by_type(&self, param_type: &str) -> Option<&NameResolver> {
        self.resolvers
            .iter()
            .find(|resolver| resolver.param_type == param_type)
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
        // 各リゾルバで順番にマッチを試行し、最初にマッチしたものを返す
        for resolver in &self.resolvers {
            if let Some(value) = resolver.resolve(arg) {
                return vec![(resolver.param_type.clone(), value)];
            }
        }
        vec![]
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
            matched_args[i].iter().any(|(arg_type, _)| arg_type == param_type)
        })
    }

    fn get_patterns(&self, pattern_type: fn(&CommandPattern) -> &Option<Vec<Vec<String>>>, args_len: usize) -> Vec<&Vec<String>> {
        COMMAND_CONFIG.commands.values()
            .filter_map(|cmd| pattern_type(cmd).as_ref())
            .flat_map(|patterns| patterns.iter())
            .filter(|pattern| pattern.len() == args_len)
            .collect()
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

        // TODO: マッチしたパターンからParsedCommandを構築

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

    #[test]
    fn test_name_resolver_basic() {
        let mut resolver = NameResolver::new("test".to_string());
        resolver.register_alias("original", "alias");
        
        assert_eq!(resolver.resolve("alias"), Some("original".to_string()));
        assert_eq!(resolver.resolve("nonexistent"), None);
    }

    #[test]
    fn test_name_resolver_multiple_aliases() {
        let mut resolver = NameResolver::new("test".to_string());
        resolver.register_alias("original", "alias1");
        resolver.register_alias("original", "alias2");
        
        assert_eq!(resolver.resolve("alias1"), Some("original".to_string()));
        assert_eq!(resolver.resolve("alias2"), Some("original".to_string()));
    }

    #[test]
    fn test_name_resolvers_from_config() {
        let resolvers = NameResolvers::new();
        
        // コマンドの解決をテスト
        if let Some(resolver) = resolvers.get_by_type("command") {
            assert!(resolver.resolve("test").is_some());
            assert!(resolver.resolve("t").is_some());
            assert_eq!(resolver.resolve("test"), Some("test".to_string()));
            assert_eq!(resolver.resolve("t"), Some("test".to_string()));
        } else {
            panic!("commandリゾルバが見つかりません");
        }

        // サイトの解決をテスト
        if let Some(resolver) = resolvers.get_by_type("site") {
            assert!(resolver.resolve("atcoder").is_some());
            assert!(resolver.resolve("ac").is_some());
            assert_eq!(resolver.resolve("atcoder"), Some("atcoder".to_string()));
            assert_eq!(resolver.resolve("ac"), Some("atcoder".to_string()));
        } else {
            panic!("siteリゾルバが見つかりません");
        }

        // 言語の解決をテスト
        if let Some(resolver) = resolvers.get_by_type("language") {
            assert!(resolver.resolve("rust").is_some());
            assert!(resolver.resolve("rs").is_some());
            assert_eq!(resolver.resolve("rust"), Some("rust".to_string()));
            assert_eq!(resolver.resolve("rs"), Some("rust".to_string()));
        } else {
            panic!("languageリゾルバが見つかりません");
        }
    }

    #[test]
    fn test_name_resolvers_priority() {
        let resolvers = NameResolvers::new();
        
        // 同じエイリアスが異なるリゾルバに存在する場合のテスト
        let matches = resolvers.find_matches("rs");
        assert!(!matches.is_empty(), "マッチが見つかりません");
        
        // インデックスが小さい（優先度が高い）順にマッチが返されることを確認
        let mut last_index = 0;
        for (index, _) in &matches {
            assert!(*index >= last_index, "優先順位が正しくありません");
            last_index = *index;
        }
    }

    #[test]
    fn test_name_resolver_case_sensitivity() {
        let resolvers = NameResolvers::new();
        
        // 大文字小文字を区別することを確認
        if let Some(resolver) = resolvers.get_by_type("site") {
            let result = resolver.resolve("AtcodeR");
            if result.is_some() {
                dbg!(&resolver.aliases);  // エイリアスの内容を表示（失敗時のみ）
                assert!(
                    result.is_none(),
                    "大文字小文字の区別が正しくありません。aliases: {:?}", 
                    resolver.aliases
                );
            }

            let result = resolver.resolve("ATCODER");
            if result.is_some() {
                dbg!(&resolver.aliases);  // エイリアスの内容を表示（失敗時のみ）
                assert!(
                    result.is_none(),
                    "大文字小文字の区別が正しくありません。aliases: {:?}", 
                    resolver.aliases
                );
            }

            let result = resolver.resolve("atcoder");
            if result.is_none() {
                dbg!(&resolver.aliases);  // エイリアスの内容を表示（失敗時のみ）
                assert!(
                    result.is_some(),
                    "小文字のエイリアスが見つかりません。aliases: {:?}", 
                    resolver.aliases
                );
            }
        }

        // 言語の大文字小文字の区別も確認
        if let Some(resolver) = resolvers.get_by_type("language") {
            let result = resolver.resolve("Python");
            if result.is_some() {
                dbg!(&resolver.aliases);  // エイリアスの内容を表示（失敗時のみ）
                assert!(
                    result.is_none(),
                    "大文字小文字の区別が正しくありません。aliases: {:?}", 
                    resolver.aliases
                );
            }

            let result = resolver.resolve("PYTHON");
            if result.is_some() {
                dbg!(&resolver.aliases);  // エイリアスの内容を表示（失敗時のみ）
                assert!(
                    result.is_none(),
                    "大文字小文字の区別が正しくありません。aliases: {:?}", 
                    resolver.aliases
                );
            }

            let result = resolver.resolve("python");
            if result.is_none() {
                dbg!(&resolver.aliases);  // エイリアスの内容を表示（失敗時のみ）
                assert!(
                    result.is_some(),
                    "小文字のエイリアスが見つかりません。aliases: {:?}", 
                    resolver.aliases
                );
            }
        }
    }

    #[test]
    fn test_name_resolver_underscore_handling() {
        let resolvers = NameResolvers::new();
        
        // アンダースコアで始まるセクションが無視されることを確認
        for resolver in resolvers.resolvers.iter() {
            for (alias, _) in resolver.aliases.iter() {
                assert!(!alias.starts_with('_'), "アンダースコアで始まるエイリアスが含まれています");
            }
        }
    }

    #[test]
    fn test_parameter_types_loaded() {
        let resolvers = NameResolvers::new();
        
        // 必須のパラメータタイプが存在することを確認
        let required_types = ["command", "site", "language", "contest", "problem"];
        for &required_type in required_types.iter() {
            assert!(
                resolvers.get_by_type(required_type).is_some(),
                "必須のパラメータタイプ {} が見つかりません",
                required_type
            );
        }
    }

    #[test]
    fn test_name_resolver_duplicate_aliases() {
        let mut resolver = NameResolver::new("test".to_string());
        
        // 同じエイリアスを異なる名前に登録した場合、後者が優先されることを確認
        resolver.register_alias("name1", "alias");
        resolver.register_alias("name2", "alias");
        
        assert_eq!(resolver.resolve("alias"), Some("name2".to_string()));
    }

    #[test]
    fn test_config_loading() {
        // 設定ファイルが正しく読み込まれていることを確認
        assert!(CONFIG.get("languages").is_some(), "languages セクションが見つかりません");
        assert!(CONFIG.get("sites").is_some(), "sites セクションが見つかりません");
        assert!(CONFIG.get("system").is_some(), "system セクションが見つかりません");

        // コマンド設定が正しく読み込まれていることを確認
        assert!(!COMMAND_CONFIG.parameter_types.is_empty(), "parameter_types が空です");
        assert!(!COMMAND_CONFIG.commands.is_empty(), "commands が空です");

        // 言語設定のエイリアスが正しく読み込まれていることを確認
        if let Some(languages) = CONFIG.get("languages") {
            if let Some(rust) = languages.get("rust") {
                if let Some(aliases) = rust.get("aliases") {
                    if let Some(aliases) = aliases.as_sequence() {
                        assert!(!aliases.is_empty(), "rust の aliases が空です");
                        assert!(aliases.iter().any(|a| a.as_str() == Some("rs")), "rust の alias 'rs' が見つかりません");
                    } else {
                        panic!("rust の aliases が配列ではありません");
                    }
                } else {
                    panic!("rust の aliases フィールドが見つかりません");
                }
            } else {
                panic!("rust 言語の設定が見つかりません");
            }
        } else {
            panic!("languages セクションが見つかりません");
        }

        // サイト設定のエイリアスが正しく読み込まれていることを確認
        if let Some(sites) = CONFIG.get("sites") {
            if let Some(atcoder) = sites.get("atcoder") {
                if let Some(aliases) = atcoder.get("aliases") {
                    if let Some(aliases) = aliases.as_sequence() {
                        assert!(!aliases.is_empty(), "atcoder の aliases が空です");
                        assert!(aliases.iter().any(|a| a.as_str() == Some("ac")), "atcoder の alias 'ac' が見つかりません");
                    } else {
                        panic!("atcoder の aliases が配列ではありません");
                    }
                } else {
                    panic!("atcoder の aliases フィールドが見つかりません");
                }
            } else {
                panic!("atcoder サイトの設定が見つかりません");
            }
        } else {
            panic!("sites セクションが見つかりません");
        }
    }

    #[test]
    fn test_basic_command_parsing() {
        let resolvers = NameResolvers::new();
        
        // 基本的なコマンドのパース
        let result = resolvers.parse_command("test a.rs").unwrap();
        assert_eq!(result.command, Some("test".to_string()));
        assert_eq!(result.problem_id, Some("a".to_string()));
        
        // サイトIDを含むコマンド
        let result = resolvers.parse_command("ac test b.rs").unwrap();
        assert_eq!(result.command, Some("test".to_string()));
        assert_eq!(result.site_id, Some("atcoder".to_string()));
        assert_eq!(result.problem_id, Some("b".to_string()));
    }

    #[test]
    fn test_input_normalization() {
        let resolvers = NameResolvers::new();
        
        // 空入力のテスト
        assert!(resolvers.normalize_input("").is_err());
        assert!(resolvers.normalize_input("   ").is_err());
        
        // 基本的な正規化
        assert_eq!(
            resolvers.normalize_input("test a.rs").unwrap(),
            vec!["test", "a.rs"]
        );
        
        // 連続する空白の正規化
        assert_eq!(
            resolvers.normalize_input("test   a.rs").unwrap(),
            vec!["test", "a.rs"]
        );
        
        // 前後の空白の除去
        assert_eq!(
            resolvers.normalize_input("  test a.rs  ").unwrap(),
            vec!["test", "a.rs"]
        );
        
        // タブと空白の混在
        assert_eq!(
            resolvers.normalize_input("test\t \ta.rs").unwrap(),
            vec!["test", "a.rs"]
        );
    }

    #[test]
    #[ignore]
    fn test_find_matches_for_arg() {
        let resolvers = NameResolvers::new();
        
        // コマンドのマッチング
        let matches = resolvers.find_matches_for_arg("test");
        assert!(!matches.is_empty(), "コマンドのマッチが見つかりません");
        assert_eq!(matches.len(), 1, "コマンドに対して複数のマッチが返されています");
        assert_eq!(matches[0], ("command".to_string(), "test".to_string()));

        // サイトIDのマッチング
        let matches = resolvers.find_matches_for_arg("ac");
        assert!(!matches.is_empty(), "サイトIDのマッチが見つかりません");
        assert_eq!(matches.len(), 1, "サイトIDに対して複数のマッチが返されています");
        assert_eq!(matches[0], ("site".to_string(), "atcoder".to_string()));

        // 言語のマッチング
        let matches = resolvers.find_matches_for_arg("rs");
        assert!(!matches.is_empty(), "言語のマッチが見つかりません");
        assert_eq!(matches.len(), 1, "言語に対して複数のマッチが返されています");
        assert_eq!(matches[0], ("language".to_string(), "rust".to_string()));

        // 存在しない入力のテスト
        let matches = resolvers.find_matches_for_arg("nonexistent");
        assert!(matches.is_empty(), "存在しない入力に対してマッチが返されています");

        // コマンドとして解釈されるべき入力が他の型とマッチしないことを確認
        let matches = resolvers.find_matches_for_arg("submit");
        assert_eq!(matches.len(), 1, "コマンドに対して複数のマッチが返されています");
        assert_eq!(matches[0], ("command".to_string(), "submit".to_string()));
    }

    #[test]
    fn test_pattern_matching() {
        let resolvers = NameResolvers::new();
        
        // 基本的なパターンマッチング
        let result = resolvers.parse_command("test a.rs").unwrap();
        assert_eq!(result.command, Some("test".to_string()));
        assert_eq!(result.problem_id, Some("a".to_string()));
        
        // 順序が重要なパターン
        let result = resolvers.parse_command("ac test a.rs").unwrap();
        assert_eq!(result.site_id, Some("atcoder".to_string()));
        assert_eq!(result.command, Some("test".to_string()));
        assert_eq!(result.problem_id, Some("a".to_string()));
        
        // 無効なパターン
        let result = resolvers.parse_command("a.rs test");
        assert!(result.is_err(), "無効なパターンがエラーを返していません");
    }

    #[test]
    fn test_check_pattern_matches() {
        let resolvers = NameResolvers::new();
        
        // テスト用のマッチ結果を作成
        let matched_args = vec![
            vec![("command".to_string(), "test".to_string())],
            vec![("problem_id".to_string(), "a".to_string())],
        ];

        // 正しいパターンのテスト
        let pattern = vec!["command".to_string(), "problem_id".to_string()];
        assert!(resolvers.check_pattern_matches(&pattern, &matched_args));

        // 順序が異なるパターンのテスト
        let wrong_pattern = vec!["problem_id".to_string(), "command".to_string()];
        assert!(!resolvers.check_pattern_matches(&wrong_pattern, &matched_args));

        // 長さが異なるパターンのテスト
        let long_pattern = vec!["command".to_string(), "problem_id".to_string(), "site".to_string()];
        assert!(!resolvers.check_pattern_matches(&long_pattern, &matched_args));

        // 存在しないパラメータタイプのテスト
        let invalid_pattern = vec!["command".to_string(), "invalid_type".to_string()];
        assert!(!resolvers.check_pattern_matches(&invalid_pattern, &matched_args));

        // 複数のマッチを含む引数のテスト
        let multi_matched_args = vec![
            vec![
                ("command".to_string(), "test".to_string()),
                ("site".to_string(), "atcoder".to_string()),
            ],
            vec![("problem_id".to_string(), "a".to_string())],
        ];
        let pattern = vec!["command".to_string(), "problem_id".to_string()];
        assert!(resolvers.check_pattern_matches(&pattern, &multi_matched_args));
    }

    #[test]
    fn test_get_patterns() {
        let resolvers = NameResolvers::new();
        
        // 順序付きパターンのテスト
        let ordered_patterns = resolvers.get_patterns(|cmd| &cmd.ordered, 2);
        assert!(!ordered_patterns.is_empty(), "順序付きパターンが見つかりません");
        
        // パターンの内容の検証
        assert!(ordered_patterns.iter().any(|pattern| {
            pattern.contains(&"{command}".to_string()) && pattern.contains(&"{problem_id}".to_string())
        }), "期待されるパターンが含まれていません");

        // 存在しない長さのパターンのテスト
        let no_patterns = resolvers.get_patterns(|cmd| &cmd.ordered, 10);
        assert!(no_patterns.is_empty(), "存在しない長さのパターンが返されています");
    }

    #[test]
    fn test_name_resolver_config_loading() {
        // commandタイプのリゾルバのテスト
        let mut resolver = NameResolver::new("command".to_string());
        resolver.load_aliases_from_config(&CONFIG);
        
        // commands.yamlから正しく読み込めているか確認
        assert!(resolver.resolve("test").is_some(), "testコマンドが読み込まれていません");
        assert!(resolver.resolve("t").is_some(), "testコマンドのエイリアスが読み込まれていません");
        assert_eq!(resolver.resolve("test"), Some("test".to_string()));
        assert_eq!(resolver.resolve("t"), Some("test".to_string()));

        // siteタイプのリゾルバのテスト
        let mut resolver = NameResolver::new("site".to_string());
        resolver.load_aliases_from_config(&CONFIG);
        
        // config.yamlから正しく読み込めているか確認
        assert!(resolver.resolve("atcoder").is_some(), "atcoderサイトが読み込まれていません");
        assert!(resolver.resolve("ac").is_some(), "atcoderサイトのエイリアスが読み込まれていません");
        assert_eq!(resolver.resolve("atcoder"), Some("atcoder".to_string()));
        assert_eq!(resolver.resolve("ac"), Some("atcoder".to_string()));
    }

    #[test]
    fn test_name_resolver_invalid_config() {
        // 存在しない設定キーのテスト
        let mut resolver = NameResolver::new("invalid_type".to_string());
        resolver.load_aliases_from_config(&CONFIG);
        assert!(resolver.aliases.is_empty(), "存在しない設定キーでエイリアスが登録されています");

        // 無効な設定値のテスト
        let invalid_config: serde_yaml::Value = serde_yaml::from_str("invalid: true").unwrap();
        let mut resolver = NameResolver::new("site".to_string());
        resolver.load_aliases_from_config(&invalid_config);
        assert!(resolver.aliases.is_empty(), "無効な設定でエイリアスが登録されています");
    }

    #[test]
    fn test_name_resolvers_empty_input() {
        let resolvers = NameResolvers::new();
        
        // 空の入力に対するfind_matches_for_argのテスト
        let matches = resolvers.find_matches_for_arg("");
        assert!(matches.is_empty(), "空の入力に対してマッチが返されています");

        // 空白文字のみの入力に対するテスト
        let matches = resolvers.find_matches_for_arg("   ");
        assert!(matches.is_empty(), "空白文字のみの入力に対してマッチが返されています");
    }
} 