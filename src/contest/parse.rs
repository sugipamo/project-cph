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

        // param_typeをクローンして所有権の問題を回避
        let target_type = self.param_type.clone();
        if cfg!(test) && std::env::var("TEST_DEBUG").is_ok() {
            println!("Starting recursive search for aliases of type: {}", target_type);
        }
        // config.yamlから再帰的にaliasesを探索
        self.load_aliases_recursive(config, &target_type);
        if cfg!(test) && std::env::var("TEST_DEBUG").is_ok() {
            println!("Finished loading aliases for type: {}", self.param_type);
            println!("Current aliases: {:?}", self.aliases);
        }
    }

    fn load_aliases_recursive(&mut self, value: &serde_yaml::Value, target_type: &str) {
        // エイリアス登録のロジックをクロージャとして定義
        let register_aliases = |resolver: &mut NameResolver, value: &serde_yaml::Value, name: &str| {
            // 元の名前自体をエイリアスとして登録
            if cfg!(test) && std::env::var("TEST_DEBUG").is_ok() {
                println!("Registering original name as alias: {} -> {}", name, name);
            }
            resolver.register_alias(name, name);

            if let Some(aliases) = value.get("aliases") {
                if cfg!(test) && std::env::var("TEST_DEBUG").is_ok() {
                    println!("Found aliases field for {}: {:?}", name, aliases);
                }
                if let Some(aliases) = aliases.as_sequence() {
                    for alias in aliases {
                        if let Some(alias) = alias.as_str() {
                            if cfg!(test) && std::env::var("TEST_DEBUG").is_ok() {
                                println!("Registering alias: {} -> {}", alias, name);
                            }
                            resolver.register_alias(name, alias);
                        }
                    }
                }
            }
        };

        match value {
            serde_yaml::Value::Mapping(map) => {
                // アンダースコアで始まるキーは無視
                for (key, value) in map {
                    if let Some(key) = key.as_str() {
                        if key.starts_with('_') {
                            continue;
                        }
                        if cfg!(test) && std::env::var("TEST_DEBUG").is_ok() {
                            println!("Checking key: {}", key);
                        }

                        // parameter_typesから設定のキーを取得
                        let config_key = COMMAND_CONFIG.parameter_types.iter()
                            .find(|pt| pt.name == target_type)
                            .and_then(|pt| pt.config_key.as_ref())
                            .map(|s| s.as_str())
                            .unwrap_or(key);

                        // 設定のキーが一致する場合、エイリアスを登録
                        if config_key == key {
                            if let Some(items) = value.as_mapping() {
                                for (name, item_value) in items {
                                    if let Some(name) = name.as_str() {
                                        if !name.starts_with('_') {
                                            register_aliases(self, item_value, name);
                                        }
                                    }
                                }
                            }
                        } else {
                            // 再帰的に探索
                            self.load_aliases_recursive(value, target_type);
                        }
                    }
                }
            }
            serde_yaml::Value::Sequence(seq) => {
                if cfg!(test) && std::env::var("TEST_DEBUG").is_ok() {
                    println!("Checking sequence");
                }
                for value in seq {
                    self.load_aliases_recursive(value, target_type);
                }
            }
            _ => {}
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
} 