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

use std::fs;
use std::sync::Arc;
use std::time::SystemTime;
use serde::{Deserialize, Serialize};
use serde_yaml::{self, Value};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ConfigError {
    #[error("設定ファイルが見つかりません: {0}")]
    NotFound(String),

    #[error("設定ファイルの読み込みに失敗しました: {0}")]
    Read(String),

    #[error("設定ファイルの解析に失敗しました: {0}")]
    Parse(String),

    #[error("設定値の型が不正です: {expected:?} が必要ですが {actual:?} が指定されています")]
    TypeError {
        expected: ConfigType,
        actual: ConfigType,
    },

    #[error("設定の検証に失敗しました: {0}")]
    Validation(String),

    #[error("{0}")]
    Config(String),
}

#[derive(Debug, Clone)]
pub enum ConfigType {
    String,
    StringArray,
    Object,
    Boolean,
    Number,
    Null,
    Tagged,
}

#[derive(Debug, Clone)]
pub struct ConfigAccess {
    path: String,
    timestamp: SystemTime,
    value_type: ConfigType,
}

pub type ConfigResult<T> = Result<T, ConfigError>;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfigValue {
    system: Value,
    languages: Value,
}

#[derive(Clone)]
pub struct Config {
    value: Arc<ConfigValue>,
    access_history: Arc<Vec<ConfigAccess>>,
    validation_rules: Arc<Vec<Arc<dyn Fn(&ConfigValue) -> ConfigResult<()> + Send + Sync>>>,
}

impl std::fmt::Debug for Config {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Config")
            .field("value", &self.value)
            .field("access_history", &self.access_history)
            .field("validation_rules", &format!("<{} rules>", self.validation_rules.len()))
            .finish()
    }
}

impl Config {
    pub fn new() -> ConfigResult<Self> {
        let config_str = fs::read_to_string("config.yml")
            .map_err(|e| ConfigError::Config(format!("設定ファイルの読み込みに失敗しました: {}", e)))?;

        let value: ConfigValue = serde_yaml::from_str(&config_str)
            .map_err(|e| ConfigError::Config(format!("設定ファイルのパースに失敗しました: {}", e)))?;

        let config = Self {
            value: Arc::new(value),
            access_history: Arc::new(Vec::new()),
            validation_rules: Arc::new(Vec::new()),
        };

        config.validate()?;
        Ok(config)
    }

    fn with_access(&self, path: String, value_type: ConfigType) -> Self {
        let mut history = (*self.access_history).clone();
        history.push(ConfigAccess {
            path,
            timestamp: SystemTime::now(),
            value_type,
        });
        Self {
            value: self.value.clone(),
            access_history: Arc::new(history),
            validation_rules: self.validation_rules.clone(),
        }
    }

    pub fn with_validation_rule<F>(self, rule: F) -> Self
    where
        F: Fn(&ConfigValue) -> ConfigResult<()> + Send + Sync + 'static,
    {
        let mut rules = (*self.validation_rules).clone();
        rules.push(Arc::new(rule));
        Self {
            value: self.value,
            access_history: self.access_history,
            validation_rules: Arc::new(rules),
        }
    }

    pub fn validate(&self) -> ConfigResult<()> {
        for rule in self.validation_rules.iter() {
            rule(&self.value)?;
        }
        Ok(())
    }

    pub fn get<T: serde::de::DeserializeOwned>(&self, path: &str) -> ConfigResult<(T, Self)> {
        let parts: Vec<&str> = path.split('.').collect();
        let mut current = match parts[0] {
            "system" => serde_yaml::to_value(&self.value.system)
                .map_err(|e| ConfigError::Config(e.to_string()))?,
            "languages" => serde_yaml::to_value(&self.value.languages)
                .map_err(|e| ConfigError::Config(e.to_string()))?,
            _ => return Err(ConfigError::Config(format!("無効な設定パス: {}", path))),
        };

        for &part in &parts[1..] {
            current = current.get(part)
                .ok_or_else(|| ConfigError::Config(format!("設定パス{}が見つかりません", path)))?
                .clone();
        }

        let value_type = match current {
            Value::String(_) => ConfigType::String,
            Value::Sequence(_) => ConfigType::StringArray,
            Value::Mapping(_) => ConfigType::Object,
            Value::Bool(_) => ConfigType::Boolean,
            Value::Number(_) => ConfigType::Number,
            Value::Null => ConfigType::Null,
            Value::Tagged(_) => ConfigType::Tagged,
        };

        let new_config = self.with_access(path.to_string(), value_type);
        let value = serde_yaml::from_value(current)
            .map_err(|e| ConfigError::Config(format!("値の変換に失敗しました: {}", e)))?;

        Ok((value, new_config))
    }

    pub fn get_with_alias<T: serde::de::DeserializeOwned>(&self, path: &str) -> ConfigResult<(T, Self)> {
        match self.get::<T>(path) {
            Ok(result) => Ok(result),
            Err(_) => {
                let parts: Vec<&str> = path.split('.').collect();
                if parts.len() >= 2 && parts[0] == "languages" {
                    let alias_path = format!("languages.{}.alias", parts[1]);
                    let (alias, config) = self.get::<String>(&alias_path)?;
                    let new_path = format!("languages.{}.{}", alias, parts[2..].join("."));
                    config.get::<T>(&new_path)
                } else {
                    Err(ConfigError::Config(format!("設定パスが見つかりません: {}", path)))
                }
            }
        }
    }

    pub fn get_raw_value(&self, key: &str) -> ConfigResult<(&Value, Self)> {
        let value = self.value.system.get(key)
            .ok_or_else(|| ConfigError::Config(format!("設定キーが見つかりません: {}", key)))?;

        let value_type = match value {
            Value::String(_) => ConfigType::String,
            Value::Sequence(_) => ConfigType::StringArray,
            Value::Mapping(_) => ConfigType::Object,
            Value::Bool(_) => ConfigType::Boolean,
            Value::Number(_) => ConfigType::Number,
            Value::Null => ConfigType::Null,
            Value::Tagged(_) => ConfigType::Tagged,
        };

        let new_config = self.with_access(key.to_string(), value_type);
        Ok((value, new_config))
    }

    pub fn access_history(&self) -> &[ConfigAccess] {
        &self.access_history
    }

    pub fn get_accesses_since(&self, since: SystemTime) -> Vec<ConfigAccess> {
        self.access_history
            .iter()
            .filter(|access| access.timestamp >= since)
            .cloned()
            .collect()
    }

    pub fn merge(&self, other: &Config) -> ConfigResult<Self> {
        let merged_value = self.merge_values(&self.value, &other.value)?;
        let mut merged_rules = (*self.validation_rules).clone();
        merged_rules.extend((*other.validation_rules).clone());

        let config = Self {
            value: Arc::new(merged_value),
            access_history: Arc::new(Vec::new()),
            validation_rules: Arc::new(merged_rules),
        };

        config.validate()?;
        Ok(config)
    }

    fn merge_values(&self, base: &ConfigValue, other: &ConfigValue) -> ConfigResult<ConfigValue> {
        let merged_system = self.merge_yaml(&base.system, &other.system)?;
        let merged_languages = self.merge_yaml(&base.languages, &other.languages)?;

        Ok(ConfigValue {
            system: merged_system,
            languages: merged_languages,
        })
    }

    fn merge_yaml(&self, base: &Value, other: &Value) -> ConfigResult<Value> {
        match (base, other) {
            (Value::Mapping(base_map), Value::Mapping(other_map)) => {
                let mut merged = base_map.clone();
                for (key, value) in other_map {
                    merged.insert(key.clone(), value.clone());
                }
                Ok(Value::Mapping(merged))
            },
            (_, other) => Ok(other.clone()),
        }
    }
} 