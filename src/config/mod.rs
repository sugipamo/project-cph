// Configuration Module
//
// # 型変換機能
// このモジュールは、YAML設定から様々な型への変換をサポートしています：
//
// ## 基本的な型変換
// ```rust
// // 文字列として取得
// let value: String = config.get("system.source_file.solution")?;
// 
// // 数値として取得
// let timeout: i64 = config.get("system.docker.timeout_seconds")?;
// let memory: f64 = config.get("system.docker.memory_limit_mb")?;
// 
// // 真偽値として取得（"yes", "true", "on", "1" は true として扱われます）
// let auto_yes: bool = config.get("system.submit.auto_yes")?;
// 
// // 文字列配列として取得
// let aliases: Vec<String> = config.get("languages.rust.aliases")?;
// ```
//
// ## エイリアス解決付きの型変換
// ```rust
// // エイリアスを解決して値を取得
// // 例: "rs.extension" -> "languages.rust.extension"
// let ext: String = config.get_with_alias("rs.extension")?;
// ```
//
// ## 型変換エラー処理
// ```rust
// // エラーハンドリングの例
// match config.get::<bool>("some.string.value") {
//     Ok(value) => println!("値: {}", value),
//     Err(ConfigError::TypeError { path, value, .. }) => {
//         println!("型変換エラー - パス: {}, 値: {}", path, value);
//     }
//     Err(e) => println!("その他のエラー: {}", e),
// }
// ```
//
// ## カスタム型の実装
// 新しい型のサポートを追加するには、`TypedValue` トレイトを実装します：
// ```rust
// impl TypedValue for MyType {
//     const TYPE: ConfigType = ConfigType::String;  // 適切な型を指定
//
//     fn from_yaml(value: &Value) -> Result<Self, ConfigError> {
//         // 値の変換ロジックを実装
//     }
// }
// ```

use std::collections::HashMap;
use serde_yaml::Value;
use std::io;
use std::env;
use regex::Regex;

#[derive(Debug, Clone, PartialEq)]
pub enum ConfigType {
    String,
    Integer,
    Float,
    Boolean,
    StringArray,
}

#[derive(Debug)]
pub enum ConfigError {
    IoError(io::Error),
    ParseError(serde_yaml::Error),
    TypeError {
        expected: ConfigType,
        found: &'static str,
        path: String,
        value: String,
    },
    PathError(String),
    AliasError(String),
    EnvError(String),
}

impl From<io::Error> for ConfigError {
    fn from(err: io::Error) -> Self {
        ConfigError::IoError(err)
    }
}

impl From<serde_yaml::Error> for ConfigError {
    fn from(err: serde_yaml::Error) -> Self {
        ConfigError::ParseError(err)
    }
}

#[derive(Debug, Clone)]
pub enum ConfigValue {
    String(String),
    Integer(i64),
    Float(f64),
    Boolean(bool),
    StringArray(Vec<String>),
}

pub trait TypedValue: Sized {
    const TYPE: ConfigType;
    fn from_yaml(value: &Value) -> Result<Self, ConfigError>;
}

pub struct AliasSection {
    path: String,
    alias_field: String,
}

pub struct ConfigBuilder {
    alias_sections: Vec<AliasSection>,
    anchor_prefix: String,
}

impl ConfigBuilder {
    pub fn new() -> Self {
        Self {
            alias_sections: Vec::new(),
            anchor_prefix: String::from("_"),
        }
    }

    pub fn add_alias_section(mut self, path: &str, alias_field: &str) -> Self {
        self.alias_sections.push(AliasSection {
            path: path.to_string(),
            alias_field: alias_field.to_string(),
        });
        self
    }

    pub fn set_anchor_prefix(mut self, prefix: &str) -> Self {
        self.anchor_prefix = prefix.to_string();
        self
    }

    pub fn build(self) -> Config {
        Config {
            data: Value::Null,
            alias_map: HashMap::new(),
            alias_sections: self.alias_sections,
            anchor_prefix: self.anchor_prefix,
        }
    }
}

pub struct Config {
    data: Value,
    alias_map: HashMap<String, String>,
    alias_sections: Vec<AliasSection>,
    anchor_prefix: String,
}

impl Config {
    pub fn builder() -> Result<Self, ConfigError> {
        let config_path = "src/config/config.yaml";
        Self::from_file(config_path, ConfigBuilder::new())
    }

    pub fn from_file(path: &str, mut builder: ConfigBuilder) -> Result<Self, ConfigError> {
        let contents = std::fs::read_to_string(path)?;
        let contents = Self::expand_env_vars(&contents)?;
        let data: Value = serde_yaml::from_str(&contents)?;
        
        // YAMLファイルからエイリアスセクションを自動検出
        if let Value::Mapping(mapping) = &data {
            for (key, value) in mapping {
                if let (Value::String(section_name), Value::Mapping(section_data)) = (key, value) {
                    // セクション内のエントリを確認
                    for (_, entry) in section_data {
                        if let Value::Mapping(entry_data) = entry {
                            // aliasesフィールドを持つエントリを見つけたら、そのセクションをエイリアスセクションとして追加
                            if entry_data.contains_key("aliases") {
                                builder = builder.add_alias_section(section_name, "aliases");
                                break;
                            }
                        }
                    }
                }
            }
        }

        let mut config = Config {
            data,
            alias_map: HashMap::new(),
            alias_sections: builder.alias_sections,
            anchor_prefix: builder.anchor_prefix,
        };
        config.build_alias_map()?;
        Ok(config)
    }

    fn expand_env_vars(content: &str) -> Result<String, ConfigError> {
        let re = Regex::new(r"\$\{([^}]+?)(?::[-=]([^}]+))?\}").unwrap();
        let mut result = content.to_string();
        let mut last_end = 0;

        while let Some(cap) = re.captures(&result[last_end..]) {
            let full_match = cap.get(0).unwrap();
            let var_name = &cap[1];
            let default_value = cap.get(2).map(|m| m.as_str());
            
            let var_value = match env::var(var_name) {
                Ok(value) => value,
                Err(_) => {
                    if let Some(default) = default_value {
                        default.to_string()
                    } else {
                        return Err(ConfigError::EnvError(
                            format!("環境変数 '{}' が見つからず、デフォルト値も指定されていません", var_name)
                        ));
                    }
                }
            };
            
            let start = last_end + full_match.start();
            let end = last_end + full_match.end();
            result.replace_range(start..end, &var_value);
            last_end = start + var_value.len();
        }
        
        Ok(result)
    }

    fn get_raw(&self, path: &str) -> Result<&Value, ConfigError> {
        let mut current = &self.data;

        for part in path.split('.') {
            current = current.get(part).ok_or_else(|| {
                ConfigError::PathError(format!("Path not found: {}", path))
            })?;
        }

        Ok(current)
    }

    pub fn get<T: TypedValue>(&self, path: &str) -> Result<T, ConfigError> {
        let value = self.get_raw(path)?;
        T::from_yaml(value).map_err(|e| match e {
            ConfigError::TypeError { expected, found, .. } => ConfigError::TypeError {
                expected,
                found,
                path: path.to_string(),
                value: Self::value_to_string(value),
            },
            _ => e,
        })
    }

    pub fn get_with_alias<T: TypedValue>(&self, path: &str) -> Result<T, ConfigError> {
        let resolved_path = self.resolve_alias_path(path);
        self.get::<T>(&resolved_path)
    }

    fn build_alias_map(&mut self) -> Result<(), ConfigError> {
        for section in &self.alias_sections {
            if let Some(section_data) = self.data.get(&section.path) {
                if let Some(mapping) = section_data.as_mapping() {
                    for (name, config) in mapping {
                        if let Some(name) = name.as_str() {
                            if name.starts_with(&self.anchor_prefix) {
                                continue; // アンカーをスキップ
                            }
                            if let Some(aliases) = config.get(&section.alias_field) {
                                if let Some(aliases) = aliases.as_sequence() {
                                    for alias in aliases {
                                        if let Some(alias) = alias.as_str() {
                                            self.alias_map.insert(
                                                alias.to_lowercase(),
                                                format!("{}.{}", section.path, name),
                                            );
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        Ok(())
    }

    fn resolve_alias_path(&self, path: &str) -> String {
        let mut parts = path.split('.');
        
        if let Some(first) = parts.next() {
            // 最初の部分がエイリアスかどうかをチェック
            if let Some(resolved) = self.alias_map.get(&first.to_lowercase()) {
                if let Some(rest) = parts.next() {
                    // 残りのパスがある場合は結合
                    let remaining: String = parts.fold(rest.to_string(), |acc, part| {
                        acc + "." + part
                    });
                    format!("{}.{}", resolved, remaining)
                } else {
                    // エイリアスのみの場合
                    resolved.clone()
                }
            } else {
                path.to_string()
            }
        } else {
            path.to_string()
        }
    }

    fn get_value_type_name(value: &Value) -> &'static str {
        match value {
            Value::Null => "null",
            Value::Bool(_) => "boolean",
            Value::Number(_) => "number",
            Value::String(_) => "string",
            Value::Sequence(_) => "array",
            Value::Mapping(_) => "object",
            Value::Tagged(_) => "tagged",
        }
    }

    fn value_to_string(value: &Value) -> String {
        match value {
            Value::Null => "null".to_string(),
            Value::Bool(b) => b.to_string(),
            Value::Number(n) => n.to_string(),
            Value::String(s) => s.clone(),
            Value::Sequence(seq) => format!("[{}]", seq.iter()
                .map(|v| Self::value_to_string(v))
                .collect::<Vec<_>>()
                .join(", ")),
            Value::Mapping(map) => format!("{{{}}}", map.iter()
                .map(|(k, v)| format!("{}: {}", 
                    Self::value_to_string(k), 
                    Self::value_to_string(v)))
                .collect::<Vec<_>>()
                .join(", ")),
            Value::Tagged(tag) => format!("!{} {}", 
                tag.tag, 
                Self::value_to_string(&tag.value)),
        }
    }
}

// 基本的な型の実装
impl TypedValue for String {
    const TYPE: ConfigType = ConfigType::String;

    fn from_yaml(value: &Value) -> Result<Self, ConfigError> {
        match value {
            Value::String(s) => Ok(s.clone()),
            Value::Number(n) => Ok(n.to_string()),
            Value::Bool(b) => Ok(b.to_string()),
            _ => Err(ConfigError::TypeError {
                expected: Self::TYPE,
                found: Config::get_value_type_name(value),
                path: String::new(),
                value: Config::value_to_string(value),
            }),
        }
    }
}

impl TypedValue for bool {
    const TYPE: ConfigType = ConfigType::Boolean;

    fn from_yaml(value: &Value) -> Result<Self, ConfigError> {
        match value {
            Value::Bool(b) => Ok(*b),
            Value::String(s) => match s.to_lowercase().as_str() {
                "true" | "yes" | "on" | "1" => Ok(true),
                "false" | "no" | "off" | "0" => Ok(false),
                _ => Err(ConfigError::TypeError {
                    expected: Self::TYPE,
                    found: "invalid boolean string",
                    path: String::new(),
                    value: s.clone(),
                }),
            },
            _ => Err(ConfigError::TypeError {
                expected: Self::TYPE,
                found: Config::get_value_type_name(value),
                path: String::new(),
                value: Config::value_to_string(value),
            }),
        }
    }
}

impl TypedValue for Vec<String> {
    const TYPE: ConfigType = ConfigType::StringArray;

    fn from_yaml(value: &Value) -> Result<Self, ConfigError> {
        value.as_sequence()
            .ok_or_else(|| ConfigError::TypeError {
                expected: Self::TYPE,
                found: Config::get_value_type_name(value),
                path: String::new(),
                value: Config::value_to_string(value),
            })?
            .iter()
            .map(|v| String::from_yaml(v))
            .collect()
    }
}

// 数値型の実装
impl TypedValue for i64 {
    const TYPE: ConfigType = ConfigType::Integer;

    fn from_yaml(value: &Value) -> Result<Self, ConfigError> {
        match value {
            Value::Number(n) => n.as_i64().ok_or_else(|| ConfigError::TypeError {
                expected: Self::TYPE,
                found: "float",
                path: String::new(),
                value: Config::value_to_string(value),
            }),
            _ => Err(ConfigError::TypeError {
                expected: Self::TYPE,
                found: Config::get_value_type_name(value),
                path: String::new(),
                value: Config::value_to_string(value),
            }),
        }
    }
}

impl TypedValue for f64 {
    const TYPE: ConfigType = ConfigType::Float;

    fn from_yaml(value: &Value) -> Result<Self, ConfigError> {
        match value {
            Value::Number(n) => n.as_f64().ok_or_else(|| ConfigError::TypeError {
                expected: Self::TYPE,
                found: "non-float number",
                path: String::new(),
                value: Config::value_to_string(value),
            }),
            _ => Err(ConfigError::TypeError {
                expected: Self::TYPE,
                found: Config::get_value_type_name(value),
                path: String::new(),
                value: Config::value_to_string(value),
            }),
        }
    }
}

impl std::fmt::Display for ConfigError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ConfigError::IoError(err) => write!(f, "ファイル操作エラー: {}", err),
            ConfigError::ParseError(err) => write!(f, "YAML解析エラー: {}", err),
            ConfigError::TypeError { expected, found, path, value } => {
                write!(f, "型エラー: パス '{}' で {} が必要ですが、{} ({}) が見つかりました",
                    path,
                    match expected {
                        ConfigType::String => "文字列",
                        ConfigType::Integer => "整数",
                        ConfigType::Float => "浮動小数点数",
                        ConfigType::Boolean => "真偽値",
                        ConfigType::StringArray => "文字列配列",
                    },
                    match *found {
                        "string" => "文字列",
                        "number" => "数値",
                        "float" => "浮動小数点数",
                        "integer" => "整数",
                        "boolean" => "真偽値",
                        "array" => "配列",
                        "null" => "null",
                        "object" => "オブジェクト",
                        "tagged" => "タグ付き値",
                        _ => found,
                    },
                    value
                )
            },
            ConfigError::PathError(path) => write!(f, "パスエラー: パス '{}' が見つかりません", path),
            ConfigError::AliasError(msg) => write!(f, "エイリアスエラー: {}", msg),
            ConfigError::EnvError(msg) => write!(f, "環境変数エラー: {}", msg),
        }
    }
}

impl std::error::Error for ConfigError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            ConfigError::IoError(err) => Some(err),
            ConfigError::ParseError(err) => Some(err),
            _ => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_config(yaml: &str) -> Config {
        let data: Value = serde_yaml::from_str(yaml).unwrap();
        let builder = Config::builder()
            .add_alias_section("languages", "aliases")
            .add_alias_section("sites", "aliases");
        
        Config {
            data,
            alias_map: HashMap::new(),
            alias_sections: builder.alias_sections,
            anchor_prefix: builder.anchor_prefix,
        }
    }

    #[test]
    fn test_alias_resolution() {
        let yaml = r#"
languages:
  rust:
    aliases: ["rs"]
    extension: "rs"
  python:
    aliases: ["py", "python3"]
    extension: "py"
sites:
  atcoder:
    aliases: ["ac"]
    url: "https://atcoder.jp"
"#;
        let mut config = create_test_config(yaml);
        config.build_alias_map().unwrap();

        // 言語エイリアスのテスト
        assert_eq!(
            config.resolve_alias_path("rs.extension"),
            "languages.rust.extension"
        );
        assert_eq!(
            config.resolve_alias_path("python3.extension"),
            "languages.python.extension"
        );

        // サイトエイリアスのテスト
        assert_eq!(
            config.resolve_alias_path("ac.url"),
            "sites.atcoder.url"
        );
    }

    #[test]
    fn test_custom_alias_section() {
        let yaml = r#"
custom:
  item1:
    shortcuts: ["i1", "item"]
    value: 42
"#;
        let data: Value = serde_yaml::from_str(yaml).unwrap();
        let mut config = Config::builder()
            .add_alias_section("custom", "shortcuts")
            .set_anchor_prefix("$")
            .build();
        
        config.data = data;
        config.build_alias_map().unwrap();

        assert_eq!(
            config.resolve_alias_path("i1.value"),
            "custom.item1.value"
        );
    }

    #[test]
    fn test_env_var_expansion() {
        // 基本的な環境変数の展開
        env::set_var("TEST_VAR", "test_value");
        let content = "key: ${TEST_VAR}";
        let expanded = Config::expand_env_vars(content).unwrap();
        assert_eq!(expanded, "key: test_value");
    }

    #[test]
    fn test_env_var_with_default() {
        // デフォルト値を使用した展開
        env::remove_var("NONEXISTENT_VAR");
        let content = "key: ${NONEXISTENT_VAR:-default_value}";
        let expanded = Config::expand_env_vars(content).unwrap();
        assert_eq!(expanded, "key: default_value");
    }

    #[test]
    fn test_env_var_with_assign_default() {
        // := 形式のデフォルト値
        env::remove_var("ASSIGN_VAR");
        let content = "key: ${ASSIGN_VAR:=assigned_value}";
        let expanded = Config::expand_env_vars(content).unwrap();
        assert_eq!(expanded, "key: assigned_value");
    }

    #[test]
    fn test_multiple_env_vars() {
        // 複数の環境変数の展開
        env::set_var("FIRST_VAR", "first");
        env::set_var("SECOND_VAR", "second");
        let content = "first: ${FIRST_VAR}\nsecond: ${SECOND_VAR}";
        let expanded = Config::expand_env_vars(content).unwrap();
        assert_eq!(expanded, "first: first\nsecond: second");
    }

    #[test]
    fn test_missing_env_var_no_default() {
        // デフォルト値なしで環境変数が見つからない場合
        env::remove_var("MISSING_VAR");
        let content = "key: ${MISSING_VAR}";
        let result = Config::expand_env_vars(content);
        assert!(result.is_err());
        if let Err(ConfigError::EnvError(msg)) = result {
            assert!(msg.contains("MISSING_VAR"));
        } else {
            panic!("期待されるエラーが発生しませんでした");
        }
    }

    #[test]
    fn test_nested_env_vars() {
        // ネストされた環境変数の展開
        env::set_var("OUTER", "outer");
        env::set_var("INNER", "inner");
        let content = "nested: ${OUTER}_${INNER}";
        let expanded = Config::expand_env_vars(content).unwrap();
        assert_eq!(expanded, "nested: outer_inner");
    }

    #[test]
    fn test_alias_case_insensitive() {
        let yaml = r#"
languages:
  rust:
    aliases: ["RS"]
    extension: "rs"
"#;
        let data: Value = serde_yaml::from_str(yaml).unwrap();
        let mut config = Config::builder()
            .add_alias_section("languages", "aliases")
            .build();
        
        config.data = data;
        config.build_alias_map().unwrap();

        // 大文字小文字を区別しないことのテスト
        assert_eq!(
            config.resolve_alias_path("rs.extension"),
            "languages.rust.extension"
        );
        assert_eq!(
            config.resolve_alias_path("RS.extension"),
            "languages.rust.extension"
        );
    }

    #[test]
    fn test_numeric_values() {
        let yaml = r#"
values:
  integer: 42
  float: 3.14
  string_number: "123"
  invalid_number: "not a number"
"#;
        let data: Value = serde_yaml::from_str(yaml).unwrap();
        let config = Config::builder().build();
        let mut config = config;
        config.data = data;

        // 整数値のテスト
        let integer: i64 = config.get("values.integer").unwrap();
        assert_eq!(integer, 42);

        // 浮動小数点値のテスト
        let float: f64 = config.get("values.float").unwrap();
        assert!((float - 3.14).abs() < f64::EPSILON);

        // 文字列から数値への変換は失敗するべき
        let string_number_result: Result<i64, _> = config.get("values.string_number");
        assert!(string_number_result.is_err());

        // 無効な数値のテスト
        let invalid_result: Result<f64, _> = config.get("values.invalid_number");
        assert!(invalid_result.is_err());
    }

    #[test]
    fn test_type_conversion() {
        let yaml = r#"
values:
  string: "hello"
  number_string: "123"
  bool_string_true: "yes"
  bool_string_false: "off"
  integer: 42
  float: 3.14
  boolean: true
"#;
        let data: Value = serde_yaml::from_str(yaml).unwrap();
        let config = Config::builder().build();
        let mut config = config;
        config.data = data;

        // 文字列型の変換テスト
        let string: String = config.get("values.string").unwrap();
        assert_eq!(string, "hello");

        // 数値からの文字列変換
        let num_str: String = config.get("values.integer").unwrap();
        assert_eq!(num_str, "42");

        // 文字列からのブール値変換
        let bool_true: bool = config.get("values.bool_string_true").unwrap();
        assert!(bool_true);
        let bool_false: bool = config.get("values.bool_string_false").unwrap();
        assert!(!bool_false);

        // エラーケースのテスト
        let invalid_bool: Result<bool, _> = config.get("values.string");
        match invalid_bool {
            Err(ConfigError::TypeError { path, value, .. }) => {
                assert_eq!(path, "values.string");
                assert_eq!(value, "hello");
            }
            _ => panic!("期待されるエラーが発生しませんでした"),
        }

        // 数値の型変換エラー
        let invalid_int: Result<i64, _> = config.get("values.float");
        match invalid_int {
            Err(ConfigError::TypeError { path, value, .. }) => {
                assert_eq!(path, "values.float");
                assert_eq!(value, "3.14");
            }
            _ => panic!("期待されるエラーが発生しませんでした"),
        }
    }

    #[test]
    fn test_error_messages() {
        let yaml = r#"
values:
  string: "hello"
  number: 42
  boolean: true
  array: ["a", "b", "c"]
"#;
        let data: Value = serde_yaml::from_str(yaml).unwrap();
        let config = Config::builder().build();
        let mut config = config;
        config.data = data;

        // 型エラーメッセージのテスト
        let bool_error: Result<bool, _> = config.get("values.string");
        assert_eq!(
            bool_error.unwrap_err().to_string(),
            "型エラー: パス 'values.string' で 真偽値 が必要ですが、文字列 (hello) が見つかりました"
        );

        // パスエラーメッセージのテスト
        let missing_error: Result<String, _> = config.get("values.nonexistent");
        assert_eq!(
            missing_error.unwrap_err().to_string(),
            "パスエラー: パス 'values.nonexistent' が見つかりません"
        );

        // 配列型エラーメッセージのテスト
        let array_error: Result<Vec<String>, _> = config.get("values.number");
        assert_eq!(
            array_error.unwrap_err().to_string(),
            "型エラー: パス 'values.number' で 文字列配列 が必要ですが、数値 (42) が見つかりました"
        );

        // 環境変数エラーメッセージのテスト
        let env_error = Config::expand_env_vars("${NONEXISTENT_VAR}");
        assert_eq!(
            env_error.unwrap_err().to_string(),
            "環境変数エラー: 環境変数 'NONEXISTENT_VAR' が見つからず、デフォルト値も指定されていません"
        );
    }
} 