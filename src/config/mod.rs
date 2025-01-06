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
use crate::docker::error::{DockerError, DockerResult};
use std::time::Duration;

#[derive(Debug, Deserialize, Clone, Serialize)]
pub struct Config {
    system: SystemConfig,
    languages: std::collections::HashMap<String, LanguageConfig>,
}

#[derive(Debug, Deserialize, Clone, Serialize)]
struct SystemConfig {
    docker: DockerSystemConfig,
}

#[derive(Debug, Deserialize, Clone, Serialize)]
struct DockerSystemConfig {
    memory_limit_mb: u64,
    timeout_seconds: u64,
    mount_point: String,
    working_dir: String,
}

#[derive(Debug, Deserialize, Clone, Serialize)]
struct LanguageConfig {
    name: String,
    image: String,
    extension: String,
    compile_cmd: Option<Vec<String>>,
    run_cmd: Vec<String>,
    env_vars: Option<Vec<String>>,
}

impl Config {
    pub fn load() -> DockerResult<Self> {
        let config_str = fs::read_to_string("src/config/config.yaml")
            .map_err(|e| DockerError::Config(format!("設定ファイルの読み込みに失敗しました: {}", e)))?;
        
        serde_yaml::from_str(&config_str)
            .map_err(|e| DockerError::Config(format!("設定ファイルのパースに失敗しました: {}", e)))
    }

    pub fn get<T: ConfigValue>(&self, path: &str) -> DockerResult<T> {
        let parts: Vec<&str> = path.split('.').collect();
        let mut current = serde_yaml::Value::Mapping(serde_yaml::Mapping::new());

        // システム設定とカスタム設定をマージ
        let mut map = serde_yaml::Mapping::new();
        map.insert(
            serde_yaml::Value::String("system".to_string()),
            serde_yaml::to_value(&self.system).map_err(|e| DockerError::Config(e.to_string()))?,
        );
        map.insert(
            serde_yaml::Value::String("languages".to_string()),
            serde_yaml::to_value(&self.languages).map_err(|e| DockerError::Config(e.to_string()))?,
        );
        current = serde_yaml::Value::Mapping(map);

        // パスに従って値を取得
        for part in parts {
            current = match current {
                serde_yaml::Value::Mapping(map) => {
                    map.get(&serde_yaml::Value::String(part.to_string()))
                        .ok_or_else(|| DockerError::Config(format!("設定パス{}が見つかりません", path)))?
                        .clone()
                }
                _ => return Err(DockerError::Config(format!("無効な設定パス: {}", path))),
            };
        }

        T::from_value(current)
            .map_err(|e| DockerError::Config(format!("値の変換に失敗しました: {}", e)))
    }

    pub fn get_image(&self) -> DockerResult<String> {
        self.get_current_language()
            .map(|lang| lang.image.clone())
    }

    pub fn get_compile_cmd(&self) -> DockerResult<Option<Vec<String>>> {
        self.get_current_language()
            .map(|lang| lang.compile_cmd.clone())
    }

    pub fn get_run_cmd(&self) -> DockerResult<Vec<String>> {
        self.get_current_language()
            .map(|lang| lang.run_cmd.clone())
    }

    pub fn get_env_vars(&self) -> DockerResult<Vec<String>> {
        self.get_current_language()
            .map(|lang| lang.env_vars.clone().unwrap_or_default())
    }

    pub fn get_working_dir(&self) -> DockerResult<String> {
        Ok(self.system.docker.working_dir.clone())
    }

    pub fn get_timeout(&self) -> DockerResult<Duration> {
        Ok(Duration::from_secs(self.system.docker.timeout_seconds))
    }

    pub fn get_memory_limit(&self) -> DockerResult<u64> {
        Ok(self.system.docker.memory_limit_mb)
    }

    pub fn get_mount_point(&self) -> DockerResult<String> {
        Ok(self.system.docker.mount_point.clone())
    }

    fn get_current_language(&self) -> DockerResult<&LanguageConfig> {
        // Note: 実際の実装では現在の言語を追跡する方法が必要です
        self.languages.get("rust")
            .ok_or_else(|| DockerError::Config("言語設定が見つかりません".to_string()))
    }
} 

// 設定値の型変換トレイト
pub trait ConfigValue: Sized {
    fn from_value(value: serde_yaml::Value) -> Result<Self, String>;
}

// String型の実装
impl ConfigValue for String {
    fn from_value(value: serde_yaml::Value) -> Result<Self, String> {
        match value {
            serde_yaml::Value::String(s) => Ok(s),
            _ => Err(format!("文字列ではありません: {:?}", value)),
        }
    }
}

// Vec<String>型の実装
impl ConfigValue for Vec<String> {
    fn from_value(value: serde_yaml::Value) -> Result<Self, String> {
        match value {
            serde_yaml::Value::Sequence(seq) => {
                seq.into_iter()
                    .map(|v| match v {
                        serde_yaml::Value::String(s) => Ok(s),
                        _ => Err(format!("文字列ではありません: {:?}", v)),
                    })
                    .collect()
            }
            _ => Err(format!("配列ではありません: {:?}", value)),
        }
    }
}

// bool型の実装
impl ConfigValue for bool {
    fn from_value(value: serde_yaml::Value) -> Result<Self, String> {
        match value {
            serde_yaml::Value::Bool(b) => Ok(b),
            serde_yaml::Value::String(s) => match s.to_lowercase().as_str() {
                "true" | "yes" | "on" | "1" => Ok(true),
                "false" | "no" | "off" | "0" => Ok(false),
                _ => Err(format!("真偽値として解釈できません: {}", s)),
            },
            _ => Err(format!("真偽値ではありません: {:?}", value)),
        }
    }
}

// u64型の実装
impl ConfigValue for u64 {
    fn from_value(value: serde_yaml::Value) -> Result<Self, String> {
        match value {
            serde_yaml::Value::Number(n) => n.as_u64()
                .ok_or_else(|| format!("u64として解釈できません: {:?}", n)),
            _ => Err(format!("数値ではありません: {:?}", value)),
        }
    }
}

// i64型の実装
impl ConfigValue for i64 {
    fn from_value(value: serde_yaml::Value) -> Result<Self, String> {
        match value {
            serde_yaml::Value::Number(n) => n.as_i64()
                .ok_or_else(|| format!("i64として解釈できません: {:?}", n)),
            _ => Err(format!("数値ではありません: {:?}", value)),
        }
    }
} 