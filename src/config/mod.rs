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

    #[error("{0}")]
    Config(String),
}

#[derive(Debug)]
pub enum ConfigType {
    String,
    StringArray,
    Object,
    Boolean,
    Number,
    Null,
}

pub type ConfigResult<T> = Result<T, ConfigError>;

#[derive(Debug, Serialize, Deserialize)]
pub struct Config {
    system: Value,
    languages: Value,
}

impl Config {
    pub fn new() -> ConfigResult<Self> {
        let config_str = fs::read_to_string("config.yml")
            .map_err(|e| ConfigError::Config(format!("設定ファイルの読み込みに失敗しました: {}", e)))?;

        let config: Config = serde_yaml::from_str(&config_str)
            .map_err(|e| ConfigError::Config(format!("設定ファイルのパースに失敗しました: {}", e)))?;

        Ok(config)
    }

    pub fn get<T: serde::de::DeserializeOwned>(&self, path: &str) -> ConfigResult<T> {
        let parts: Vec<&str> = path.split('.').collect();
        let mut current = match parts[0] {
            "system" => serde_yaml::to_value(&self.system)
                .map_err(|e| ConfigError::Config(e.to_string()))?,
            "languages" => serde_yaml::to_value(&self.languages)
                .map_err(|e| ConfigError::Config(e.to_string()))?,
            _ => return Err(ConfigError::Config(format!("無効な設定パス: {}", path))),
        };

        for &part in &parts[1..] {
            current = current.get(part)
                .ok_or_else(|| ConfigError::Config(format!("設定パス{}が見つかりません", path)))?
                .clone();
        }

        serde_yaml::from_value(current)
            .map_err(|e| ConfigError::Config(format!("値の変換に失敗しました: {}", e)))
    }

    pub fn get_with_alias<T: serde::de::DeserializeOwned>(&self, path: &str) -> ConfigResult<T> {
        let result = self.get::<T>(path);
        if result.is_ok() {
            return result;
        }

        // エイリアスの解決を試みる
        let parts: Vec<&str> = path.split('.').collect();
        if parts.len() >= 2 && parts[0] == "languages" {
            let alias_path = format!("languages.{}.alias", parts[1]);
            if let Ok(alias) = self.get::<String>(&alias_path) {
                let new_path = format!("languages.{}.{}", alias, parts[2..].join("."));
                return self.get::<T>(&new_path);
            }
        }

        result
    }

    pub fn get_raw_value(&self, key: &str) -> ConfigResult<&Value> {
        self.system.get(key).ok_or_else(|| ConfigError::Config(format!("設定キーが見つかりません: {}", key)))
    }
} 