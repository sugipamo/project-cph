// Configuration Module
//
// このモジュールは、イミュータブルで型安全な設定管理を提供します。
// 主な機能：
// - 型安全な設定アクセス
// - イミュータブルな設定値
// - カスタムスキーマによるバリデーション
// - 柔軟な型変換システム
// - 設定変更の追跡

use std::sync::Arc;
use std::collections::HashMap;
use std::time::SystemTime;
use serde_yaml::Value;
use regex::Regex;

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
    listeners: Arc<Vec<Arc<dyn ConfigListener>>>,
    history: Arc<Vec<ConfigChange>>,
}

#[derive(Clone, Debug)]
pub struct ConfigChange {
    timestamp: SystemTime,
    path: String,
    old_value: Option<Arc<Value>>,
    new_value: Arc<Value>,
}

// 設定変更通知のトレイト
pub trait ConfigListener: Send + Sync {
    fn on_change(&self, old: &ConfigNode, new: &ConfigNode);
}

// エラー型
#[derive(Debug)]
pub enum ConfigError {
    PathNotFound(String),
    TypeError { expected: &'static str, found: String },
    ValidationError { message: String },
    ValueError { message: String },
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

    pub fn as_typed<T: FromConfigValue>(&self) -> ConfigResult<T> {
        T::from_config_value(&self.value)
    }

    pub fn with_value(&self, value: Value) -> ConfigResult<Self> {
        if let Some(schema) = &self.metadata.schema {
            schema.validate(&value)?;
        }
        Ok(Self {
            value: Arc::new(value),
            metadata: self.metadata.clone(),
        })
    }
}

// Configの実装
impl Config {
    pub fn new(root_value: Value) -> Self {
        Self {
            root: Arc::new(ConfigNode::new(root_value, String::from("root"))),
            listeners: Arc::new(Vec::new()),
            history: Arc::new(Vec::new()),
        }
    }

    pub fn with_listener<L: ConfigListener + 'static>(self, listener: L) -> Self {
        let mut listeners = (*self.listeners).clone();
        listeners.push(Arc::new(listener));
        Self {
            listeners: Arc::new(listeners),
            ..self
        }
    }

    fn notify_listeners(&self, old: &ConfigNode, new: &ConfigNode) {
        for listener in self.listeners.iter() {
            listener.on_change(old, new);
        }
    }

    pub fn get<T: FromConfigValue>(&self, path: &str) -> ConfigResult<T> {
        self.get_node(path).and_then(|node| node.as_typed())
    }

    fn get_node(&self, path: &str) -> ConfigResult<ConfigNode> {
        self.resolve_path(path)
            .map(|value| ConfigNode::new(value, path.to_string()))
    }
}

// ConfigAccessの実装
impl ConfigAccess for Config {
    fn get(&self, path: &str) -> ConfigResult<ConfigNode> {
        self.get_node(path)
    }

    fn get_all(&self, pattern: &str) -> ConfigResult<Vec<ConfigNode>> {
        self.find_matching_paths(pattern)
            .into_iter()
            .map(|path| self.get(&path))
            .collect()
    }

    fn exists(&self, path: &str) -> bool {
        self.resolve_path(path).is_ok()
    }
}

// 基本型のFromConfigValue実装
impl FromConfigValue for String {
    fn from_config_value(value: &Value) -> ConfigResult<Self> {
        match value {
            Value::String(s) => Ok(s.clone()),
            Value::Number(n) => Ok(n.to_string()),
            Value::Bool(b) => Ok(b.to_string()),
            _ => Err(ConfigError::TypeError {
                expected: "string-convertible",
                found: value.type_str().to_string(),
            }),
        }
    }
}

impl FromConfigValue for bool {
    fn from_config_value(value: &Value) -> ConfigResult<Self> {
        match value {
            Value::Bool(b) => Ok(*b),
            Value::String(s) => match s.to_lowercase().as_str() {
                "true" | "yes" | "on" | "1" => Ok(true),
                "false" | "no" | "off" | "0" => Ok(false),
                _ => Err(ConfigError::ValueError {
                    message: format!("無効な真偽値: {}", s),
                }),
            },
            _ => Err(ConfigError::TypeError {
                expected: "boolean",
                found: value.type_str().to_string(),
            }),
        }
    }
}

impl FromConfigValue for i64 {
    fn from_config_value(value: &Value) -> ConfigResult<Self> {
        match value {
            Value::Number(n) => n.as_i64().ok_or_else(|| ConfigError::ValueError {
                message: "数値が範囲外です".to_string(),
            }),
            Value::String(s) => s.parse().map_err(|_| ConfigError::ValueError {
                message: format!("無効な数値: {}", s),
            }),
            _ => Err(ConfigError::TypeError {
                expected: "number",
                found: value.type_str().to_string(),
            }),
        }
    }
}

// ヘルパーメソッド
impl Config {
    fn resolve_path(&self, path: &str) -> ConfigResult<Value> {
        let parts: Vec<&str> = path.split('.').collect();
        let mut current = self.root.value.clone();
        
        for part in parts {
            match &*current {
                Value::Mapping(map) => {
                    current = Arc::new(map.get(part).ok_or_else(|| ConfigError::PathNotFound(
                        path.to_string(),
                    ))?.clone());
                }
                _ => return Err(ConfigError::PathNotFound(path.to_string())),
            }
        }
        
        Ok((*current).clone())
    }

    fn find_matching_paths(&self, _pattern: &str) -> Vec<String> {
        // TODO: 実装
        vec![]
    }
}

pub trait ValueExt {
    fn type_str(&self) -> &'static str;
}

impl std::fmt::Display for ConfigError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ConfigError::PathNotFound(path) => write!(f, "パスが見つかりません: {}", path),
            ConfigError::TypeError { expected, found } => 
                write!(f, "型エラー: 期待される型 {}, 実際の型 {}", expected, found),
            ConfigError::ValidationError { message } => 
                write!(f, "バリデーションエラー: {}", message),
            ConfigError::ValueError { message } => 
                write!(f, "値エラー: {}", message),
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
            ConfigSchema::Primitive(ptype) => match (ptype, value) {
                (PrimitiveType::String, Value::String(_)) => Ok(()),
                (PrimitiveType::Number, Value::Number(_)) => Ok(()),
                (PrimitiveType::Boolean, Value::Bool(_)) => Ok(()),
                (PrimitiveType::Null, Value::Null) => Ok(()),
                _ => Err(ConfigError::TypeError {
                    expected: ptype.type_str(),
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
            },
            ConfigSchema::Object(fields) => {
                if let Value::Mapping(map) = value {
                    for (key, schema) in fields {
                        if let Some(field_value) = map.get(key) {
                            schema.validate(field_value)?;
                        }
                    }
                    Ok(())
                } else {
                    Err(ConfigError::TypeError {
                        expected: "object",
                        found: value.type_str().to_string(),
                    })
                }
            },
            ConfigSchema::Union(schemas) => {
                for schema in schemas {
                    if schema.validate(value).is_ok() {
                        return Ok(());
                    }
                }
                Err(ConfigError::ValidationError {
                    message: "値がユニオン型のいずれにも一致しません".to_string(),
                })
            },
            ConfigSchema::Custom(schema) => schema.validate(value),
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
        Ok(ConfigNode {
            value: Arc::new(value.clone()),
            metadata: Arc::new(ConfigMetadata {
                path: String::new(),
                schema: None,
                description: None,
            }),
        })
    }
} 