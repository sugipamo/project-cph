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

// 必須設定値の定義を構造体として追加
#[derive(Debug, Clone)]
pub struct RequiredValue {
    pub path: String,
    pub description: String,
    pub config_type: ConfigType,
}

impl RequiredValue {
    pub fn new(path: &str, description: &str, config_type: ConfigType) -> Self {
        Self {
            path: path.to_string(),
            description: description.to_string(),
            config_type,
        }
    }
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
    RequiredValueError(String),
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

impl std::error::Error for ConfigError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            ConfigError::IoError(err) => Some(err),
            ConfigError::ParseError(err) => Some(err),
            _ => None,
        }
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

#[derive(Debug, Clone)]
pub struct AliasSection {
    path: String,
    alias_field: String,
}

pub struct ConfigBuilder {
    alias_sections: Vec<AliasSection>,
    anchor_prefix: String,
    required_values: Vec<RequiredValue>,  // 必須設定値のリストを追加
}

impl ConfigBuilder {
    pub fn new() -> Self {
        Self {
            alias_sections: Vec::new(),
            anchor_prefix: String::from("_"),
            required_values: Vec::new(),
        }
    }

    // 必須設定値を追加するメソッド
    pub fn add_required_value(mut self, path: &str, description: &str, config_type: ConfigType) -> Self {
        self.required_values.push(RequiredValue::new(path, description, config_type));
        self
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
            required_values: self.required_values,
        }
    }
}

#[derive(Debug, Clone)]
pub struct Config {
    data: Value,
    alias_map: HashMap<String, String>,
    alias_sections: Vec<AliasSection>,
    anchor_prefix: String,
    required_values: Vec<RequiredValue>,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            data: Value::Null,
            alias_map: HashMap::new(),
            alias_sections: Vec::new(),
            anchor_prefix: String::from("_"),
            required_values: Vec::new(),
        }
    }
}

impl Config {
    pub fn builder() -> ConfigBuilder {
        ConfigBuilder::new()
    }

    pub fn load() -> Result<Self, ConfigError> {
        let config_path = "src/config/config.yaml";
        let builder = ConfigBuilder::new();
        Self::from_file(config_path, builder)
    }

    pub fn from_file(path: &str, builder: ConfigBuilder) -> Result<Self, ConfigError> {
        let contents = std::fs::read_to_string(path)?;
        let contents = Self::expand_env_vars(&contents)?;
        let data: Value = serde_yaml::from_str(&contents)?;
        
        // YAMLファイルからエイリアスセクションを自動検出
        let mut builder = builder;
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
            required_values: builder.required_values,
        };
        config.build_alias_map()?;
        config.validate_required_values()?;  // 必須設定値を検証
        Ok(config)
    }

    pub fn load_from_file(path: &str) -> Result<Self, ConfigError> {
        let contents = std::fs::read_to_string(path)?;
        let contents = Self::expand_env_vars(&contents)?;
        let data: Value = serde_yaml::from_str(&contents)?;
        
        Ok(Self {
            data,
            alias_map: HashMap::new(),
            alias_sections: Vec::new(),
            anchor_prefix: String::from("_"),
            required_values: Vec::new(),
        })
    }

    fn expand_env_vars(content: &str) -> Result<String, ConfigError> {
        let re = Regex::new(r"\$\{([^}-]+)(?:-([^}]+))?\}").unwrap();
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
                            format!("環境変数 '{}' が未設定で、デフォルト値も指定されていません", var_name)
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
                ConfigError::PathError(path.to_string())
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

    pub fn get_with_message<T: TypedValue>(&self, path: &str, error_message: &str) -> Result<T, ConfigError> {
        self.get_raw(path)
            .map_err(|_| ConfigError::RequiredValueError(error_message.to_string()))
            .and_then(|value| T::from_yaml(value).map_err(|e| match e {
                ConfigError::TypeError { expected, found, .. } => ConfigError::TypeError {
                    expected,
                    found,
                    path: path.to_string(),
                    value: Self::value_to_string(value),
                },
                _ => e,
            }))
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

    pub fn validate_required_values(&self) -> Result<(), ConfigError> {
        for required in &self.required_values {
            if let Err(ConfigError::PathError(_)) = self.get_raw(&required.path) {
                return Err(ConfigError::RequiredValueError(
                    format!("必須設定 '{}' ({}) が設定されていません", required.path, required.description)
                ));
            }
            // 型チェックも行う
            match required.config_type {
                ConfigType::String => { let _: String = self.get(&required.path)?; },
                ConfigType::Integer => { let _: i64 = self.get(&required.path)?; },
                ConfigType::Float => { let _: f64 = self.get(&required.path)?; },
                ConfigType::Boolean => { let _: bool = self.get(&required.path)?; },
                ConfigType::StringArray => { let _: Vec<String> = self.get(&required.path)?; },
            }
        }
        Ok(())
    }

    pub fn get_raw_value(&self, path: &str) -> Result<&Value, ConfigError> {
        let parts: Vec<&str> = path.split('.').collect();
        let mut current = &self.data;

        for part in parts {
            if let Value::Mapping(map) = current {
                if let Some(value) = map.get(&Value::String(part.to_string())) {
                    current = value;
                } else {
                    return Err(ConfigError::PathError(path.to_string()));
                }
            } else {
                return Err(ConfigError::PathError(path.to_string()));
            }
        }

        Ok(current)
    }

    pub fn from_str(content: &str, builder: ConfigBuilder) -> Result<Self, ConfigError> {
        let contents = Self::expand_env_vars(content)?;
        let data: Value = serde_yaml::from_str(&contents)?;
        
        // YAMLファイルからエイリアスセクションを自動検出
        let mut builder = builder;
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
            required_values: builder.required_values,
        };
        config.build_alias_map()?;
        config.validate_required_values()?;  // 必須設定値を検証
        Ok(config)
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

impl TypedValue for u64 {
    const TYPE: ConfigType = ConfigType::Integer;

    fn from_yaml(value: &Value) -> Result<Self, ConfigError> {
        match value {
            Value::Number(n) => {
                if let Some(i) = n.as_i64() {
                    if i < 0 {
                        Err(ConfigError::TypeError {
                            expected: Self::TYPE,
                            found: "negative integer",
                            path: String::new(),
                            value: Config::value_to_string(value),
                        })
                    } else {
                        Ok(i as u64)
                    }
                } else {
                    Err(ConfigError::TypeError {
                        expected: Self::TYPE,
                        found: "non-integer number",
                        path: String::new(),
                        value: Config::value_to_string(value),
                    })
                }
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
            ConfigError::PathError(path) => write!(f, "設定エラー: パス '{}' が見つかりません", path),
            ConfigError::AliasError(msg) => write!(f, "エイリアスエラー: {}", msg),
            ConfigError::EnvError(msg) => write!(f, "環境変数エラー: {}", msg),
            ConfigError::RequiredValueError(msg) => write!(f, "設定エラー: {}", msg),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_config(yaml: &str) -> Config {
        let contents = Config::expand_env_vars(yaml).unwrap();
        let data: Value = serde_yaml::from_str(&contents).unwrap();
        let mut config = Config {
            data,
            alias_map: HashMap::new(),
            alias_sections: vec![],
            anchor_prefix: String::from("_"),
            required_values: vec![],
        };
        config.build_alias_map().unwrap();
        config
    }

    #[test]
    fn test_env_var_expansion() {
        std::env::set_var("TEST_VAR", "test_value");
        let yaml = "${TEST_VAR}";
        let result = Config::expand_env_vars(yaml).unwrap();
        assert_eq!(result, "test_value");
    }

    #[test]
    fn test_env_var_with_default() {
        let yaml = "${NONEXISTENT_VAR-default_value}";
        let result = Config::expand_env_vars(yaml).unwrap();
        assert_eq!(result, "default_value");
    }

    #[test]
    fn test_env_var_with_assign_default() {
        let yaml = "${NONEXISTENT_VAR-default_value}";
        let result = Config::expand_env_vars(yaml).unwrap();
        assert_eq!(result, "default_value");
    }

    #[test]
    fn test_multiple_env_vars() {
        std::env::set_var("VAR1", "value1");
        std::env::set_var("VAR2", "value2");
        let yaml = "${VAR1} ${VAR2}";
        let result = Config::expand_env_vars(yaml).unwrap();
        assert_eq!(result, "value1 value2");
    }

    #[test]
    fn test_missing_env_var_no_default() {
        let yaml = "${NONEXISTENT_VAR}";
        let env_error = Config::expand_env_vars(yaml);
        assert!(env_error.is_err());
        assert_eq!(
            env_error.unwrap_err().to_string(),
            "環境変数エラー: 環境変数 'NONEXISTENT_VAR' が未設定で、デフォルト値も指定されていません"
        );
    }

    #[test]
    fn test_nested_env_vars() {
        std::env::set_var("OUTER", "outer");
        std::env::set_var("INNER", "inner");
        let yaml = "${OUTER}_${INNER}";
        let result = Config::expand_env_vars(yaml).unwrap();
        assert_eq!(result, "outer_inner");
    }

    #[test]
    fn test_numeric_values() {
        let yaml = r#"
        system:
          docker:
            timeout_seconds: 10
            memory_limit_mb: 256.5
        "#;

        let config = create_test_config(yaml);

        // 整数値の取得
        let timeout: i64 = config.get("system.docker.timeout_seconds").unwrap();
        assert_eq!(timeout, 10);

        // 浮動小数点値の取得
        let memory: f64 = config.get("system.docker.memory_limit_mb").unwrap();
        assert_eq!(memory, 256.5);

        // 型変換エラーの確認
        let error = config.get::<bool>("system.docker.timeout_seconds");
        assert!(error.is_err());
    }
} 