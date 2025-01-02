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
static CONFIG: Lazy<serde_yaml::Value> = Lazy::new(|| {
    let config_str = include_str!("../../src/config/config.yaml");
    serde_yaml::from_str(config_str).expect("設定ファイルの読み込みに失敗")
});

#[allow(dead_code)]
static COMMAND_CONFIG: Lazy<serde_yaml::Value> = Lazy::new(|| {
    let config_str = include_str!("../../src/config/commands.yaml");
    serde_yaml::from_str(config_str).expect("コマンド設定の読み込みに失敗")
});

#[allow(dead_code)]
#[derive(Debug, Clone)]
pub struct NameResolver {
    param_type: String,
    aliases: HashMap<String, String>,
}

impl NameResolver {
    pub fn new(param_type: String) -> Self {
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

#[cfg(test)]
impl NameResolver {
    pub fn get_param_type(&self) -> &str {
        &self.param_type
    }

    pub fn get_aliases_len(&self) -> usize {
        self.aliases.len()
    }

    pub fn get_alias(&self, alias: &str) -> Option<String> {
        self.aliases.get(alias).cloned()
    }

    pub fn is_empty(&self) -> bool {
        self.aliases.is_empty()
    }
}

#[allow(dead_code)]
#[derive(Debug, Clone)]
pub struct NameResolvers {
    resolvers: Vec<NameResolver>,
}

impl NameResolvers {
    pub fn new() -> Self {
        let mut resolvers = Vec::new();
        let mut resolver_map = HashMap::new();

        // parameter_typesからリゾルバの型を取得
        if let Some(parameter_types) = COMMAND_CONFIG.get("parameter_types") {
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
        for config in [&*CONFIG, &*COMMAND_CONFIG].iter() {
            let Some(map) = config.as_mapping() else { 
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
        let result = ParsedCommand::new();
        
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
        let mut matching_ordered: Vec<_> = ordered_patterns.iter()
            .filter(|pattern| self.check_pattern_matches(pattern, &matched_args))
            .collect();
        matching_ordered.sort();
        matching_ordered.dedup();
        if cfg!(test) {
            println!("マッチした順序付きパターン: {:?}", matching_ordered);
        }

        let unordered_patterns = self.get_patterns(|cmd| &cmd.unordered, args_len);
        let mut matching_unordered: Vec<_> = unordered_patterns.iter()
            .filter(|pattern| self.check_pattern_matches(pattern, &matched_args))
            .collect();
        matching_unordered.sort();
        matching_unordered.dedup();
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
