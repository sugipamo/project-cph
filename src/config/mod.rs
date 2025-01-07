// Configuration Module
//
// このモジュールは、イミュータブルで型安全な設定管理を提供します。
// 主な機能：
// - 型安全な設定アクセス
// - イミュータブルな設定値
// - カスタムスキーマによるバリデーション
// - 柔軟な型変換システム

use std::sync::Arc;
use std::collections::HashMap;
use serde_yaml::Value;
use regex::Regex;
use std::path::Path;
use std::fs;

// 基本的な設定ノード
#[derive(Clone, Debug)]
pub struct ConfigNode {
    value: Arc<Value>,
    metadata: Arc<ConfigMetadata>,
}

#[derive(Clone, Debug)]
pub struct ConfigMetadata {
    path: String,
    schema: Option<Arc<ConfigSchema>>,
    description: Option<String>,
}

// スキーマ定義
#[derive(Clone, Debug)]
pub enum ConfigSchema {
    Primitive(PrimitiveType),
    Array(Box<ConfigSchema>),
    Object(HashMap<String, ConfigSchema>),
    Union(Vec<ConfigSchema>),
    Custom(Arc<dyn CustomSchema>),
}

#[derive(Clone, Debug)]
pub enum PrimitiveType {
    String,
    Number,
    Boolean,
    Null,
}

// カスタムスキーマのトレイト
pub trait CustomSchema: Send + Sync + std::fmt::Debug {
    fn validate(&self, value: &Value) -> ConfigResult<()>;
    fn describe(&self) -> String;
}

// 設定アクセスのトレイト
pub trait ConfigAccess {
    fn get(&self, path: &str) -> ConfigResult<ConfigNode>;
    fn get_all(&self, pattern: &str) -> ConfigResult<Vec<ConfigNode>>;
    fn exists(&self, path: &str) -> bool;
}

// 型変換のトレイト
pub trait FromConfigValue: Sized {
    fn from_config_value(value: &Value) -> ConfigResult<Self>;
}

// メインの設定構造体
#[derive(Clone)]
pub struct Config {
    root: Arc<ConfigNode>,
}

// エラー型
#[derive(Debug)]
pub enum ConfigError {
    PathNotFound(String),
    TypeError { expected: &'static str, found: String },
    ValidationError { message: String },
    ValueError { message: String },
    IoError(String),
}

pub type ConfigResult<T> = Result<T, ConfigError>;

// ConfigNodeの実装
impl ConfigNode {
    pub fn new(value: Value, path: String) -> Self {
        Self {
            value: Arc::new(value),
            metadata: Arc::new(ConfigMetadata {
                path,
                schema: None,
                description: None,
            }),
        }
    }

    pub fn with_schema(mut self, schema: ConfigSchema) -> Self {
        Arc::make_mut(&mut self.metadata).schema = Some(Arc::new(schema));
        self
    }

    pub fn with_description(mut self, description: String) -> Self {
        Arc::make_mut(&mut self.metadata).description = Some(description);
        self
    }

    pub fn as_typed<T: FromConfigValue>(&self) -> ConfigResult<T> {
        T::from_config_value(&self.value)
    }
}

// Configの実装
impl Config {
    pub fn new(root_value: Value) -> Self {
        Self {
            root: Arc::new(ConfigNode::new(root_value, String::from("root"))),
        }
    }

    pub fn load_from_file<P: AsRef<Path>>(path: P) -> ConfigResult<Self> {
        let contents = fs::read_to_string(path)
            .map_err(|e| ConfigError::IoError(e.to_string()))?;
        let value = serde_yaml::from_str(&contents)
            .map_err(|e| ConfigError::ValueError { message: e.to_string() })?;
        Ok(Self::new(value))
    }

    pub fn get<T: FromConfigValue>(&self, path: &str) -> ConfigResult<T> {
        self.get_node(path)?.as_typed()
    }

    fn get_node(&self, path: &str) -> ConfigResult<ConfigNode> {
        let value = self.resolve_path(path)?;
        Ok(ConfigNode::new(value, path.to_string()))
    }

    fn resolve_path(&self, path: &str) -> ConfigResult<Value> {
        if path == "root" {
            return Ok((*self.root.value).clone());
        }

        let parts: Vec<&str> = path.split('.').collect();
        let mut current = &*self.root.value;

        for part in parts {
            match current {
                Value::Mapping(map) => {
                    current = map.get(&Value::String(part.to_string()))
                        .ok_or_else(|| ConfigError::PathNotFound(path.to_string()))?;
                }
                Value::Sequence(seq) => {
                    let index = part.parse::<usize>()
                        .map_err(|_| ConfigError::PathNotFound(path.to_string()))?;
                    current = seq.get(index)
                        .ok_or_else(|| ConfigError::PathNotFound(path.to_string()))?;
                }
                _ => return Err(ConfigError::PathNotFound(path.to_string())),
            }
        }

        Ok(current.clone())
    }
}

// ConfigAccessの実装
impl ConfigAccess for Config {
    fn get(&self, path: &str) -> ConfigResult<ConfigNode> {
        self.get_node(path)
    }

    fn get_all(&self, pattern: &str) -> ConfigResult<Vec<ConfigNode>> {
        let regex = Regex::new(pattern)
            .map_err(|e| ConfigError::ValueError { message: e.to_string() })?;

        Ok(self.find_matching_paths(pattern)
            .into_iter()
            .filter_map(|path| {
                if regex.is_match(&path) {
                    self.get_node(&path).ok()
                } else {
                    None
                }
            })
            .collect())
    }

    fn exists(&self, path: &str) -> bool {
        self.get_node(path).is_ok()
    }
}

// 基本的な型変換の実装
impl FromConfigValue for String {
    fn from_config_value(value: &Value) -> ConfigResult<Self> {
        match value {
            Value::String(s) => Ok(s.clone()),
            _ => Err(ConfigError::TypeError {
                expected: "string",
                found: value.type_str().to_string(),
            }),
        }
    }
}

impl FromConfigValue for i64 {
    fn from_config_value(value: &Value) -> ConfigResult<Self> {
        match value {
            Value::Number(n) => n.as_i64().ok_or_else(|| ConfigError::TypeError {
                expected: "integer",
                found: "non-integer number".to_string(),
            }),
            _ => Err(ConfigError::TypeError {
                expected: "number",
                found: value.type_str().to_string(),
            }),
        }
    }
}

impl FromConfigValue for bool {
    fn from_config_value(value: &Value) -> ConfigResult<Self> {
        match value {
            Value::Bool(b) => Ok(*b),
            _ => Err(ConfigError::TypeError {
                expected: "boolean",
                found: value.type_str().to_string(),
            }),
        }
    }
}

// ヘルパートレイト
pub trait ValueExt {
    fn type_str(&self) -> &'static str;
}

impl std::fmt::Display for ConfigError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ConfigError::PathNotFound(path) => write!(f, "Path not found: {}", path),
            ConfigError::TypeError { expected, found } => {
                write!(f, "Type error: expected {}, found {}", expected, found)
            }
            ConfigError::ValidationError { message } => write!(f, "Validation error: {}", message),
            ConfigError::ValueError { message } => write!(f, "Value error: {}", message),
            ConfigError::IoError(message) => write!(f, "IO error: {}", message),
        }
    }
}

impl ValueExt for Value {
    fn type_str(&self) -> &'static str {
        match self {
            Value::Null => "null",
            Value::Bool(_) => "boolean",
            Value::Number(_) => "number",
            Value::String(_) => "string",
            Value::Sequence(_) => "array",
            Value::Mapping(_) => "object",
            Value::Tagged(_) => "tagged",
        }
    }
}

impl ConfigSchema {
    pub fn validate(&self, value: &Value) -> ConfigResult<()> {
        match self {
            ConfigSchema::Primitive(primitive_type) => match (primitive_type, value) {
                (PrimitiveType::String, Value::String(_)) => Ok(()),
                (PrimitiveType::Number, Value::Number(_)) => Ok(()),
                (PrimitiveType::Boolean, Value::Bool(_)) => Ok(()),
                (PrimitiveType::Null, Value::Null) => Ok(()),
                _ => Err(ConfigError::TypeError {
                    expected: primitive_type.type_str(),
                    found: value.type_str().to_string(),
                }),
            },
            ConfigSchema::Array(item_schema) => {
                if let Value::Sequence(items) = value {
                    for item in items {
                        item_schema.validate(item)?;
                    }
                    Ok(())
                } else {
                    Err(ConfigError::TypeError {
                        expected: "array",
                        found: value.type_str().to_string(),
                    })
                }
            }
            ConfigSchema::Object(properties) => {
                if let Value::Mapping(map) = value {
                    for (key, schema) in properties {
                        if let Some(value) = map.get(&Value::String(key.clone())) {
                            schema.validate(value)?;
                        }
                    }
                    Ok(())
                } else {
                    Err(ConfigError::TypeError {
                        expected: "object",
                        found: value.type_str().to_string(),
                    })
                }
            }
            ConfigSchema::Union(schemas) => {
                for schema in schemas {
                    if schema.validate(value).is_ok() {
                        return Ok(());
                    }
                }
                Err(ConfigError::ValidationError {
                    message: "Value does not match any schema in union".to_string(),
                })
            }
            ConfigSchema::Custom(custom) => custom.validate(value),
        }
    }
}

impl PrimitiveType {
    fn type_str(&self) -> &'static str {
        match self {
            PrimitiveType::String => "string",
            PrimitiveType::Number => "number",
            PrimitiveType::Boolean => "boolean",
            PrimitiveType::Null => "null",
        }
    }
}

impl FromConfigValue for Value {
    fn from_config_value(value: &Value) -> ConfigResult<Self> {
        Ok(value.clone())
    }
}

impl FromConfigValue for ConfigNode {
    fn from_config_value(value: &Value) -> ConfigResult<Self> {
        Ok(ConfigNode::new(value.clone(), String::new()))
    }
}

// 設定を探すためのヘルパーメソッド
impl Config {
    fn find_matching_paths(&self, _pattern: &str) -> Vec<String> {
        let mut paths = Vec::new();
        self.collect_paths(&self.root.value, "root", &mut paths);
        paths
    }

    fn collect_paths(&self, value: &Value, current_path: &str, paths: &mut Vec<String>) {
        paths.push(current_path.to_string());

        match value {
            Value::Mapping(map) => {
                for (key, value) in map {
                    if let Value::String(key_str) = key {
                        let new_path = if current_path == "root" {
                            key_str.clone()
                        } else {
                            format!("{}.{}", current_path, key_str)
                        };
                        self.collect_paths(value, &new_path, paths);
                    }
                }
            }
            Value::Sequence(seq) => {
                for (i, value) in seq.iter().enumerate() {
                    let new_path = format!("{}.{}", current_path, i);
                    self.collect_paths(value, &new_path, paths);
                }
            }
            _ => {}
        }
    }
} 