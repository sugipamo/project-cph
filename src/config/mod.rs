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
use anyhow::{Error, Result, Context as _};

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
    fn validate(&self, value: &Value) -> Result<()>;
    fn describe(&self) -> String;
}

// 設定アクセスのトレイト
pub trait ConfigAccess {
    fn get(&self, path: &str) -> Result<ConfigNode>;
    fn get_all(&self, pattern: &str) -> Result<Vec<ConfigNode>>;
    fn exists(&self, path: &str) -> bool;
}

// 型変換のトレイト
pub trait FromConfigValue: Sized {
    fn from_config_value(value: &Value) -> Result<Self>;
}

// メインの設定構造体
#[derive(Clone)]
pub struct Config {
    root: Arc<ConfigNode>,
}

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

    pub fn with_schema(self, schema: ConfigSchema) -> Self {
        Self {
            value: self.value,
            metadata: Arc::new(ConfigMetadata {
                path: self.metadata.path.clone(),
                schema: Some(Arc::new(schema)),
                description: self.metadata.description.clone(),
            }),
        }
    }

    pub fn with_description(self, description: String) -> Self {
        Self {
            value: self.value,
            metadata: Arc::new(ConfigMetadata {
                path: self.metadata.path.clone(),
                schema: self.metadata.schema.clone(),
                description: Some(description),
            }),
        }
    }

    pub fn as_typed<T: FromConfigValue>(&self) -> Result<T> {
        T::from_config_value(&self.value)
    }

    pub fn key(&self) -> Result<String> {
        match &*self.value {
            Value::String(s) => Ok(s.clone()),
            _ => Err(anyhow::anyhow!("キーは文字列である必要があります")),
        }
    }
}

// Configの実装
impl Config {
    pub fn new(root_value: Value) -> Self {
        Self {
            root: Arc::new(ConfigNode::new(root_value, String::from("root"))),
        }
    }

    pub fn load_from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let contents = fs::read_to_string(&path)
            .with_context(|| format!("設定ファイルの読み込みに失敗: {}", path.as_ref().display()))?;
        let value = serde_yaml::from_str(&contents)
            .with_context(|| "YAMLのパースに失敗しました")?;
        Ok(Self::new(value))
    }

    pub fn get<T: FromConfigValue>(&self, path: &str) -> Result<T> {
        self.get_node(path)?.as_typed()
    }

    fn get_node(&self, path: &str) -> Result<ConfigNode> {
        let value = self.resolve_path(path)?;
        Ok(ConfigNode::new(value, path.to_string()))
    }

    fn resolve_path(&self, path: &str) -> Result<Value> {
        if path == "root" {
            return Ok((*self.root.value).clone());
        }

        let parts: Vec<&str> = path.split('.').collect();
        let mut current = &*self.root.value;

        for part in parts {
            match current {
                Value::Mapping(map) => {
                    current = map.get(&Value::String(part.to_string()))
                        .with_context(|| format!("パス '{}'が見つかりません", path))?;
                }
                Value::Sequence(seq) => {
                    let index = part.parse::<usize>()
                        .with_context(|| format!("無効なインデックス '{}' (パス: {})", part, path))?;
                    current = seq.get(index)
                        .with_context(|| format!("インデックス {} が範囲外です (パス: {})", index, path))?;
                }
                _ => return Err(Error::msg(format!("無効なパス: {}", path))),
            }
        }

        Ok(current.clone())
    }
}

// ConfigAccessの実装
impl ConfigAccess for Config {
    fn get(&self, path: &str) -> Result<ConfigNode> {
        self.get_node(path)
    }

    fn get_all(&self, pattern: &str) -> Result<Vec<ConfigNode>> {
        let regex = Regex::new(pattern)
            .with_context(|| format!("無効な正規表現パターン: {}", pattern))?;

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
    fn from_config_value(value: &Value) -> Result<Self> {
        match value {
            Value::String(s) => Ok(s.clone()),
            _ => Err(Error::msg(format!("文字列型を期待しましたが、{}型が見つかりました", value.type_str()))),
        }
    }
}

impl FromConfigValue for i64 {
    fn from_config_value(value: &Value) -> Result<Self> {
        match value {
            Value::Number(n) => n.as_i64()
                .with_context(|| "整数型を期待しましたが、浮動小数点数が見つかりました"),
            _ => Err(Error::msg(format!("数値型を期待しましたが、{}型が見つかりました", value.type_str()))),
        }
    }
}

impl FromConfigValue for bool {
    fn from_config_value(value: &Value) -> Result<Self> {
        match value {
            Value::Bool(b) => Ok(*b),
            _ => Err(Error::msg(format!("真偽値型を期待しましたが、{}型が見つかりました", value.type_str()))),
        }
    }
}

impl FromConfigValue for HashMap<String, String> {
    fn from_config_value(value: &Value) -> Result<Self> {
        match value {
            Value::Mapping(map) => {
                let mut result = HashMap::new();
                for (key, value) in map {
                    let key = match key {
                        Value::String(s) => s.clone(),
                        _ => return Err(anyhow::anyhow!("マップのキーは文字列である必要があります")),
                    };
                    let value = match value {
                        Value::String(s) => s.clone(),
                        _ => return Err(anyhow::anyhow!("マップの値は文字列である必要があります")),
                    };
                    result.insert(key, value);
                }
                Ok(result)
            }
            _ => Err(anyhow::anyhow!("マップ型を期待しましたが、{}型が見つかりました", value.type_str())),
        }
    }
}

// ヘルパートレイト
pub trait ValueExt {
    fn type_str(&self) -> &'static str;
}

impl std::fmt::Display for PrimitiveType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            PrimitiveType::String => write!(f, "string"),
            PrimitiveType::Number => write!(f, "number"),
            PrimitiveType::Boolean => write!(f, "boolean"),
            PrimitiveType::Null => write!(f, "null"),
        }
    }
}

impl ConfigSchema {
    pub fn validate(&self, value: &Value) -> Result<()> {
        match self {
            ConfigSchema::Primitive(primitive_type) => match (primitive_type, value) {
                (PrimitiveType::String, Value::String(_)) => Ok(()),
                (PrimitiveType::Number, Value::Number(_)) => Ok(()),
                (PrimitiveType::Boolean, Value::Bool(_)) => Ok(()),
                (PrimitiveType::Null, Value::Null) => Ok(()),
                _ => Err(Error::msg(format!(
                    "型エラー: {}型を期待しましたが、{}型が見つかりました",
                    primitive_type.type_str(),
                    value.type_str()
                ))),
            },
            ConfigSchema::Array(item_schema) => {
                if let Value::Sequence(items) = value {
                    for item in items {
                        item_schema.validate(item)?;
                    }
                    Ok(())
                } else {
                    Err(Error::msg(format!(
                        "型エラー: array型を期待しましたが、{}型が見つかりました",
                        value.type_str()
                    )))
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
                    Err(Error::msg(format!(
                        "型エラー: object型を期待しましたが、{}型が見つかりました",
                        value.type_str()
                    )))
                }
            }
            ConfigSchema::Union(schemas) => {
                for schema in schemas {
                    if schema.validate(value).is_ok() {
                        return Ok(());
                    }
                }
                Err(Error::msg("値がユニオン型のいずれにも一致しません"))
            }
            ConfigSchema::Custom(custom) => custom.validate(value),
        }
    }
}

impl FromConfigValue for Value {
    fn from_config_value(value: &Value) -> Result<Self> {
        Ok(value.clone())
    }
}

impl FromConfigValue for ConfigNode {
    fn from_config_value(value: &Value) -> Result<Self> {
        Ok(ConfigNode::new(value.clone(), String::new()))
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

impl ValueExt for PrimitiveType {
    fn type_str(&self) -> &'static str {
        match self {
            PrimitiveType::String => "string",
            PrimitiveType::Number => "number",
            PrimitiveType::Boolean => "boolean",
            PrimitiveType::Null => "null",
        }
    }
}

// 設定を探すためのヘルパーメソッド
impl Config {
    fn find_matching_paths(&self, _pattern: &str) -> Vec<String> {
        self.collect_paths(&self.root.value)
    }

    fn collect_paths(&self, value: &Value) -> Vec<String> {
        match value {
            Value::Mapping(map) => {
                map.iter()
                    .flat_map(|(key, val)| {
                        let key_str = match key {
                            Value::String(s) => s.clone(),
                            Value::Number(n) => n.to_string(),
                            Value::Bool(b) => b.to_string(),
                            Value::Null => "null".to_string(),
                            Value::Sequence(_) => "[array]".to_string(),
                            Value::Mapping(_) => "{object}".to_string(),
                            Value::Tagged(_) => "[tagged]".to_string(),
                        };
                        let key_for_sub = key_str.clone();
                        let sub_paths = self.collect_paths(val)
                            .into_iter()
                            .map(move |sub_path| {
                                if sub_path.is_empty() {
                                    key_for_sub.clone()
                                } else {
                                    format!("{}.{}", key_for_sub, sub_path)
                                }
                            });
                        std::iter::once(key_str).chain(sub_paths).collect::<Vec<_>>()
                    })
                    .collect()
            },
            Value::Sequence(seq) => {
                seq.iter()
                    .enumerate()
                    .flat_map(|(idx, val)| {
                        let idx_str = idx.to_string();
                        let idx_for_sub = idx_str.clone();
                        let sub_paths = self.collect_paths(val)
                            .into_iter()
                            .map(move |sub_path| {
                                if sub_path.is_empty() {
                                    idx_for_sub.clone()
                                } else {
                                    format!("{}.{}", idx_for_sub, sub_path)
                                }
                            });
                        std::iter::once(idx_str).chain(sub_paths).collect::<Vec<_>>()
                    })
                    .collect()
            },
            _ => vec![String::new()],
        }
    }
} 