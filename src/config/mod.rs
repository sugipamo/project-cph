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
use anyhow::{Error, Result, Context as _, anyhow};

// 基本的な設定ノード
#[derive(Clone, PartialEq, Eq, Debug)]
pub struct Node {
    value: Value,
    metadata: Metadata,
}

#[derive(Clone, PartialEq, Eq, Debug)]
pub struct Metadata {
    path: String,
    description: Option<String>,
    schema: Option<Schema>,
}

#[derive(Clone, PartialEq, Eq)]
pub struct SchemaMetadata {
    description: Option<String>,
    required: bool,
    children: HashMap<String, SchemaMetadata>,
    schema_type: SchemaType,
}

#[derive(Clone, PartialEq, Eq)]
pub enum SchemaType {
    String,
    Number,
    Boolean,
    Object(HashMap<String, Schema>),
    Array(Box<Schema>),
    Custom(String),
}

pub trait SchemaValidator: Send + Sync + std::fmt::Debug {
    /// 値を検証します
    /// 
    /// # Errors
    /// - 値が無効な場合
    /// - スキーマの制約に違反している場合
    fn validate(&self, value: &Value) -> Result<()>;
}

pub trait Access {
    /// 指定されたパスの設定値を取得します。
    /// 
    /// # Errors
    /// - パスが存在しない場合にエラーを返します。
    /// - パスの形式が無効な場合にエラーを返します。
    fn get(&self, path: &str) -> Result<Arc<Node>>;

    /// 指定されたパターンに一致する全ての設定値を取得します。
    /// 
    /// # Errors
    /// - パターンが無効な正規表現の場合にエラーを返します。
    /// - パスの形式が無効な場合にエラーを返します。
    fn get_all(&self, pattern: &str) -> Result<Vec<Arc<Node>>>;

    /// 指定されたパスの設定値が存在するかどうかを確認します。
    ///
    /// # Returns
    /// * `bool` - 設定値が存在する場合はtrue
    fn exists(&self, path: &str) -> bool;
}

// スキーマ定義
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Schema {
    Primitive(PrimitiveType),
    Array(Box<Schema>),
    Object(HashMap<String, Schema>),
    Union(Vec<Schema>),
    Custom(Arc<dyn CustomSchema>),
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PrimitiveType {
    String,
    Number,
    Boolean,
    Null,
}

// カスタムスキーマのトレイト
pub trait CustomSchema: Send + Sync + std::fmt::Debug {
    /// カスタムスキーマの検証を行います。
    /// 
    /// # Errors
    /// 
    /// 値がスキーマに適合しない場合にエラーを返します。
    fn validate(&self, value: &Value) -> Result<()>;
    
    fn describe(&self) -> String;
    fn eq(&self, other: &dyn CustomSchema) -> bool;
}

impl PartialEq for dyn CustomSchema {
    fn eq(&self, other: &Self) -> bool {
        self.eq(other)
    }
}

impl Eq for dyn CustomSchema {}

// インの設定構造体
#[derive(Clone, PartialEq, Eq, Debug)]
pub struct Config {
    root: Arc<Node>,
}

// ConfigNodeの実装
#[allow(dead_code)]
impl Node {
    /// 新しい設定ノードを作成します
    #[must_use]
    pub const fn new(value: Value, path: String) -> Self {
        Self {
            value,
            metadata: Metadata {
                path,
                description: None,
                schema: None,
            },
        }
    }

    /// スキーマを設定します
    #[must_use]
    pub fn with_schema(self, schema: Schema) -> Self {
        Self {
            value: self.value,
            metadata: Metadata {
                path: self.metadata.path,
                schema: Some(schema),
                description: self.metadata.description,
            },
        }
    }

    /// 説明を設定します
    #[must_use]
    pub fn with_description(self, description: String) -> Self {
        Self {
            value: self.value,
            metadata: Metadata {
                path: self.metadata.path,
                schema: self.metadata.schema,
                description: Some(description),
            },
        }
    }

    /// 設定値を型付きの値として取得します。
    /// 
    /// # Errors
    /// - 値の型が要求された型と一致しない場合にエラーを返します。
    /// - 値の変換に失敗した場合にエラーを返します。
    pub fn as_typed<T: FromConfigValue>(&self) -> Result<T> {
        T::from_config_value(&self.value)
    }

    #[must_use]
    pub fn as_str(&self) -> Option<&str> {
        match &self.value {
            Value::String(s) => Some(s),
            _ => None,
        }
    }

    #[must_use]
    pub fn as_i64(&self) -> Option<i64> {
        match &self.value {
            Value::Number(n) => n.as_i64(),
            _ => None,
        }
    }

    #[must_use]
    pub const fn as_bool(&self) -> Option<bool> {
        match &self.value {
            Value::Bool(b) => Some(*b),
            _ => None,
        }
    }

    #[must_use]
    pub const fn as_mapping(&self) -> Option<&serde_yaml::Mapping> {
        match &self.value {
            Value::Mapping(m) => Some(m),
            _ => None,
        }
    }

    #[must_use]
    pub const fn as_sequence(&self) -> Option<&Vec<Value>> {
        match &self.value {
            Value::Sequence(s) => Some(s),
            _ => None,
        }
    }

    /// キーを文字列として取得します。
    /// 
    /// # Errors
    /// - キーが存在しない場合にエラーを返します。
    pub fn key(&self) -> Result<String> {
        Ok(self.metadata.path.clone())
    }

    fn get_from_map(&self, parts: &[String]) -> Result<Arc<Self>> {
        match &self.value {
            Value::Mapping(map) => {
                let part = parts.first().ok_or_else(|| anyhow!("無効なパス"))?;
                let value = map.get(Value::String(part.to_string()))
                    .ok_or_else(|| anyhow!("パスが見つかりません"))?;
                if parts.len() == 1 {
                    Ok(Arc::new(Self::new(value.clone(), part.clone())))
                } else {
                    let node = Self::new(value.clone(), part.clone());
                    node.get_from_map(&parts[1..])
                }
            }
            _ => Err(anyhow!("無効なパス")),
        }
    }

    fn get_all_from_map(&self, pattern: &Regex, path: &str) -> Result<Vec<Arc<Self>>> {
        match &self.value {
            Value::Mapping(map) => {
                let mut result = Vec::new();
                for (key, value) in map {
                    if let Value::String(key_str) = key {
                        if pattern.is_match(key_str) {
                            result.push(Arc::new(Self::new(value.clone(), key_str.clone())));
                        }
                        if let Value::Mapping(_) = value {
                            let node = Self::new(value.clone(), key_str.clone());
                            let mut sub_result = node.get_all_from_map(pattern, &format!("{path}.{key_str}"))?;
                            result.append(&mut sub_result);
                        }
                    }
                }
                Ok(result)
            }
            _ => Ok(Vec::new()),
        }
    }
}

// Configの実装
impl Config {
    #[must_use]
    pub fn new(root_value: Value) -> Self {
        Self {
            root: Arc::new(Node::new(root_value, String::from("root"))),
        }
    }

    /// ファイルから設定を読み込みます。
    /// 
    /// # Errors
    /// - ファイルが存在しない場合にエラーを返します。
    /// - ファイルの形式が無効な場合にエラーを返します。
    /// - ファイルの読み込みに失敗した場合にエラーを返します。
    /// 
    /// # Panics
    /// - パスが親ディレクトリを持っていない場合にパニックします。
    pub fn load_from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let contents = fs::read_to_string(&path)
            .with_context(|| format!("設定ファイルの読み込みに失敗: {}", path.as_ref().display()))?;
        
        // メイン設定を読み込む
        let mut value = serde_yaml::from_str(&contents)
            .with_context(|| "YAMLのパースに失敗しました")?;

        // commands.yamlを読み込む
        let commands_path = path.as_ref().parent()
            .expect("パスは親ディレクトリを持っている必要があります")
            .join("commands.yaml");
        if commands_path.exists() {
            let commands_contents = fs::read_to_string(&commands_path)
                .with_context(|| format!("コマンド設定ファイルの読み込みに失敗: {}", commands_path.display()))?;
            let commands_value: Value = serde_yaml::from_str(&commands_contents)
                .with_context(|| "コマンド設定のパースに失敗しました")?;

            // メイン設定にコマンド設定をマージ
            if let Value::Mapping(ref mut map) = value {
                if let Value::Mapping(commands_map) = commands_value {
                    map.extend(commands_map);
                }
            }
        }

        Ok(Self::new(value))
    }

    /// 指定されたパスの設定値を型付きで取得します。
    /// 
    /// # Errors
    /// - パスが存在しない場合にエラーを返します。
    /// - 値の型が要求された型と一致しない場合にエラーを返します。
    pub fn get<T: FromConfigValue>(&self, path: &str) -> Result<T> {
        self.get_node(path).and_then(|node| node.as_typed())
    }

    /// 指定されたパスの設定ノードを取得します。
    /// 
    /// # Errors
    /// - パスが存在しない場合にエラーを返します。
    pub fn get_node(&self, path: &str) -> Result<Arc<Node>> {
        if path.is_empty() {
            return Ok(self.root.clone());
        }

        let parts: Vec<&str> = path.split('.').collect();
        let mut current = self.root.clone();

        for part in parts {
            match current.as_mapping() {
                Some(map) => {
                    let value = map.get(Value::String(part.to_string()))
                        .ok_or_else(|| anyhow!("設定項目が見つかりません: {}", path))?;
                    current = value.as_node()
                        .ok_or_else(|| anyhow!("無効な設定値です: {}", path))?;
                }
                None => return Err(anyhow!("無効な設定値です: {}", path)),
            }
        }
        Ok(current)
    }

    fn resolve_path(&self, path: &str) -> Result<Value> {
        if path == "root" {
            return Ok(self.root.value.clone());
        }

        let parts: Vec<&str> = path.split('.').collect();
        let mut current = &self.root.value;

        for part in parts {
            match current {
                Value::Mapping(map) => {
                    current = map.get(Value::String(part.to_string()))
                        .with_context(|| format!("パス '{path}'が見つかりません"))?;
                }
                Value::Sequence(seq) => {
                    let index = part.parse::<usize>()
                        .with_context(|| format!("無効なインデックス '{part}' (パス: {path})"))?;
                    current = seq.get(index)
                        .with_context(|| format!("インデックス {index} が範囲外です (パス: {path})"))?;
                }
                _ => return Err(Error::msg(format!("無効なパス: {path}"))),
            }
        }

        Ok(current.clone())
    }

    /// 指定されたパスの設定値を型付きで取得します。
    /// 
    /// # Errors
    /// - パスが存在しない場合にエラーを返します。
    /// - 値のシリアライズに失敗した場合にエラーを返します。
    pub fn get_typed<T: serde::de::DeserializeOwned>(&self, path: &str) -> Result<T> {
        let value = self.resolve_path(path)?;
        serde_yaml::from_value(value).map_err(|e| anyhow::anyhow!("型変換に失敗しました: {}", e))
    }

    /// 指定されたパターンに一致する全ての設定値を取得します。
    /// 
    /// # Errors
    /// - パターンが無効な正規表現の場合にエラーを返します。
    pub fn get_all(&self, pattern: &str) -> Result<Vec<Arc<Node>>> {
        let regex = Regex::new(pattern)
            .with_context(|| format!("無効な正規表現パターン: {pattern}"))?;

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
}

// ConfigAccessの実装
impl Access for Config {
    /// 指定されたパスの設定値を取得します。
    /// 
    /// # Errors
    /// - パスが存在しない場合にエラーを返します。
    /// - パスの形式が無効な場合にエラーを返します。
    fn get(&self, path: &str) -> Result<Arc<Node>> {
        self.get_node(path)
    }

    /// 指定されたパターンに一致する全ての設定値を取得します。
    /// 
    /// # Errors
    /// - パターンが無効な正規表現の場合にエラーを返します。
    /// - パスの形式が無効な場合にエラーを返します。
    fn get_all(&self, pattern: &str) -> Result<Vec<Arc<Node>>> {
        let regex = Regex::new(pattern)
            .with_context(|| format!("無効な正規表現パターン: {pattern}"))?;

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

// 型変換のトレイト
pub trait FromConfigValue: Sized {
    /// 設定値から型を生成します。
    /// 
    /// # Errors
    /// - 値の型が要求された型と一致しない場合にエラーを返します。
    /// - 値の変換に失敗した場合にエラーを返します。
    fn from_config_value(value: &Value) -> Result<Self>;
}

impl FromConfigValue for String {
    fn from_config_value(value: &Value) -> Result<Self> {
        match value {
            Value::String(s) => Ok(s.clone()),
            _ => Err(anyhow!("文字列型を期待しましたが、{}型が見つかりました", value.type_str())),
        }
    }
}

impl FromConfigValue for i64 {
    fn from_config_value(value: &Value) -> Result<Self> {
        match value {
            Value::Number(n) => n.as_i64()
                .ok_or_else(|| anyhow!("整数型を期待しましたが、浮動小数点数が見つかりました")),
            _ => Err(anyhow!("数値型を期待しましたが、{}型が見つかりました", value.type_str())),
        }
    }
}

impl FromConfigValue for bool {
    fn from_config_value(value: &Value) -> Result<Self> {
        match value {
            Value::Bool(b) => Ok(*b),
            _ => Err(anyhow!("真偽値値型を期待しましたが、{}型が見つかりました", value.type_str())),
        }
    }
}

impl<S: ::std::hash::BuildHasher + Default> FromConfigValue for HashMap<String, String, S> {
    fn from_config_value(value: &Value) -> Result<Self> {
        match value {
            Value::Mapping(map) => {
                let mut result = Self::default();
                for (key, value) in map {
                    let key = match key {
                        Value::String(s) => s.clone(),
                        _ => return Err(anyhow!("マップのキーは文字列である必要があります")),
                    };
                    let value = match value {
                        Value::String(s) => s.clone(),
                        _ => return Err(anyhow!("マップの値は文字列である必要があります")),
                    };
                    result.insert(key, value);
                }
                Ok(result)
            }
            _ => Err(anyhow!("マップ型を期待しましたが、{}型が見つかりました", value.type_str())),
        }
    }
}

impl FromConfigValue for Value {
    fn from_config_value(value: &Value) -> Result<Self> {
        Ok(value.clone())
    }
}

impl FromConfigValue for Node {
    fn from_config_value(value: &Value) -> Result<Self> {
        Ok(Self::new(value.clone(), String::new()))
    }
}

// ヘルパートレイト
pub trait ValueExt {
    fn type_str(&self) -> &'static str;
    fn as_node(&self) -> Option<Arc<Node>>;
}

impl std::fmt::Display for PrimitiveType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::String => write!(f, "string"),
            Self::Number => write!(f, "number"),
            Self::Boolean => write!(f, "boolean"),
            Self::Null => write!(f, "null"),
        }
    }
}

impl Schema {
    /// 値を検証します
    /// 
    /// # Arguments
    /// * `value` - 検証する値
    ///
    /// # Returns
    /// * `Result<()>` - 検証結果
    ///
    /// # Errors
    /// - 値の型が一致しない場合
    /// - 値が無効な場合
    /// - スキーマの制約に違反している場合
    pub fn validate(&self, value: &Value) -> Result<()> {
        match self {
            Self::Primitive(primitive_type) => match (primitive_type, value) {
                (PrimitiveType::String, Value::String(_)) |
                (PrimitiveType::Number, Value::Number(_)) |
                (PrimitiveType::Boolean, Value::Bool(_)) |
                (PrimitiveType::Null, Value::Null) => Ok(()),
                _ => Err(anyhow!("値の型が一致しません")),
            },
            Self::Array(item_schema) => {
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
            Self::Object(properties) => {
                if let Value::Mapping(map) = value {
                    for (key, schema) in properties {
                        if let Some(value) = map.get(Value::String(key.clone())) {
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
            Self::Union(schemas) => {
                for schema in schemas {
                    if schema.validate(value).is_ok() {
                        return Ok(());
                    }
                }
                Err(Error::msg("値がユニオン型のいずれにも一致しません"))
            }
            Self::Custom(custom) => custom.validate(value),
        }
    }
}

impl ValueExt for Value {
    fn type_str(&self) -> &'static str {
        match self {
            Self::Null => "null",
            Self::Bool(_) => "boolean",
            Self::Number(_) => "number",
            Self::String(_) => "string",
            Self::Sequence(_) => "array",
            Self::Mapping(_) => "object",
            Self::Tagged(_) => "tagged",
        }
    }

    fn as_node(&self) -> Option<Arc<Node>> {
        if let Self::Mapping(m) = self {
            if let Some(Self::String(node_type)) = m.get(Self::String("type".to_string())) {
                if node_type == "node" {
                    return Some(Arc::new(Node::new(self.clone(), String::new())));
                }
            }
        }
        None
    }
}

impl ValueExt for PrimitiveType {
    fn type_str(&self) -> &'static str {
        match self {
            Self::String => "string",
            Self::Number => "number",
            Self::Boolean => "boolean",
            Self::Null => "null",
        }
    }

    fn as_node(&self) -> Option<Arc<Node>> {
        None
    }
}

// 設定を探すためのヘルパーメソッド
impl Config {
    fn find_matching_paths(&self, _pattern: &str) -> Vec<String> {
        self.collect_paths(&self.root.value)
    }

    #[allow(clippy::only_used_in_recursion)]
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
                                    format!("{key_for_sub}.{sub_path}")
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
                                    format!("{idx_for_sub}.{sub_path}")
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