// Configuration Module
//
// このモジュールは、イミュータブルで型安全な設定管理を提供します。
// 主な機能：
// - 型安全な設定アクセス
// - イミュータブルな設定値
// - カスタムスキーマによるバリデーション
// - 柔軟な型変換システム

use anyhow::{anyhow, bail, Context, Result};
use serde_yaml::Value;
use std::fs;
use std::path::Path;
use std::sync::OnceLock;
use std::env;
use regex::Regex;
use once_cell::sync::Lazy;
use yaml_rust::{YamlLoader, Yaml};
use yaml_rust::yaml::Hash;

static CONFIG: OnceLock<Config> = OnceLock::new();
static ENV_VAR_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"\$\{([^}]+)}").expect("正規表現パターンが不正です")
});

#[derive(Debug, Clone)]
pub struct Config {
    data: Value,
}

impl Config {
    /// 指定されたパスから設定を読み込みます
    ///
    /// # Errors
    ///
    /// - 設定ファイルが存在しない場合
    /// - 設定ファイルの形式が不正な場合
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let path_str = path.as_ref().display().to_string();
        let content = fs::read_to_string(&path)
            .with_context(|| format!("設定ファイル '{path_str}' の読み込みに失敗しました"))?;
        
        Self::parse_str(&content)
            .with_context(|| format!("設定ファイル '{path_str}' のパースに失敗しました"))
    }

    /// 文字列から設定を作成します
    ///
    /// # Errors
    ///
    /// - YAML形式が不正な場合
    pub fn parse_str(content: &str) -> Result<Self> {
        let expanded_content = Self::expand_env_vars(content);
        
        // yaml-rustでパース
        let docs = YamlLoader::load_from_str(&expanded_content)
            .context("不正なYAML形式です")?;
        
        if docs.is_empty() {
            bail!("YAMLドキュメントが空です");
        }

        let yaml = &docs[0];
        let processed = Self::process_yaml(yaml)?;
        
        // YAMLを文字列に変換してからserde_yamlでパース
        let yaml_str = Self::yaml_to_string(&processed)?;
        let data: Value = serde_yaml::from_str(&yaml_str)
            .context("YAMLの変換に失敗しました")?;

        if !data.is_mapping() {
            bail!("YAMLのルート要素はマッピング（オブジェクト）である必要があります");
        }

        Ok(Self { data })
    }

    fn process_yaml(yaml: &Yaml) -> Result<Yaml> {
        match yaml {
            Yaml::Hash(hash) => {
                let mut result = Hash::new();
                
                // アンカーの処理
                let mut base = None;
                if let Some(Yaml::Hash(base_hash)) = hash.get(&Yaml::String("<<".to_string())) {
                    base = Some(base_hash.clone());
                }
                
                // ベースの値をコピー
                if let Some(base_hash) = base {
                    for (key, value) in base_hash {
                        result.insert(key.clone(), Self::process_yaml(&value)?);
                    }
                }
                
                // 上書き
                for (key, value) in hash {
                    if key != &Yaml::String("<<".to_string()) {
                        result.insert(key.clone(), Self::process_yaml(value)?);
                    }
                }
                
                Ok(Yaml::Hash(result))
            }
            Yaml::Array(array) => {
                let mut result = Vec::new();
                for item in array {
                    result.push(Self::process_yaml(item)?);
                }
                Ok(Yaml::Array(result))
            }
            _ => Ok(yaml.clone()),
        }
    }

    fn yaml_to_string(yaml: &Yaml) -> Result<String> {
        match yaml {
            Yaml::Hash(hash) => {
                let mut result = String::from("{");
                let mut first = true;
                for (key, value) in hash {
                    if !first {
                        result.push_str(", ");
                    }
                    first = false;
                    result.push_str(&format!("{}: {}", Self::yaml_to_string(key)?, Self::yaml_to_string(value)?));
                }
                result.push('}');
                Ok(result)
            }
            Yaml::Array(array) => {
                let mut result = String::from("[");
                let mut first = true;
                for item in array {
                    if !first {
                        result.push_str(", ");
                    }
                    first = false;
                    result.push_str(&Self::yaml_to_string(item)?);
                }
                result.push(']');
                Ok(result)
            }
            Yaml::String(s) => Ok(format!("\"{}\"", s.replace('\"', "\\\""))),
            Yaml::Integer(i) => Ok(i.to_string()),
            Yaml::Real(r) => Ok(r.to_string()),
            Yaml::Boolean(b) => Ok(b.to_string()),
            Yaml::Null => Ok("null".to_string()),
            Yaml::Alias(_) => bail!("YAMLエイリアスはサポートされていません"),
            Yaml::BadValue => bail!("不正なYAML値です"),
        }
    }

    /// 環境変数を展開します
    /// ${VAR-default} の形式で指定された環境変数を展開します
    /// VAR が設定されていない場合は default が使用されます
    fn expand_env_vars(content: &str) -> String {
        ENV_VAR_PATTERN.replace_all(content, |caps: &regex::Captures| {
            let var_spec = &caps[1];
            if let Some((var_name, default)) = var_spec.split_once('-') {
                env::var(var_name).unwrap_or_else(|_| default.to_string())
            } else {
                env::var(var_spec).unwrap_or_default()
            }
        }).to_string()
    }

    /// デフォルト設定ファイルから設定値を取得します
    ///
    /// # Arguments
    ///
    /// * `path` - ドット区切りの設定パス（例: "system.browser"）
    ///
    /// # Returns
    ///
    /// * `Result<T>` - 設定値
    ///
    /// # Errors
    ///
    /// - 設定パスが存在しない場合
    /// - 設定値の型変換に失敗した場合
    ///
    /// # Panics
    ///
    /// - デフォルト設定ファイルの読み込みに失敗した場合
    pub fn get_default<T>(path: &str) -> Result<T>
    where
        T: serde::de::DeserializeOwned,
    {
        let config = CONFIG.get_or_init(|| {
            Self::from_file("src/config/config.yaml")
                .expect("デフォルト設定ファイルの読み込みに失敗しました")
        });
        config.get(path)
    }

    /// 設定値を取得します
    ///
    /// # Arguments
    ///
    /// * `path` - ドット区切りの設定パス（例: "system.browser"）
    ///
    /// # Returns
    ///
    /// * `Result<T>` - 設定値
    ///
    /// # Errors
    ///
    /// - 設定パスが存在しない場合
    /// - 設定値の型変換に失敗した場合
    pub fn get<T>(&self, path: &str) -> Result<T>
    where
        T: serde::de::DeserializeOwned,
    {
        let parts: Vec<&str> = path.split('.').collect();
        let mut current = &self.data;

        for (i, &part) in parts.iter().enumerate() {
            current = current.get(part).ok_or_else(|| {
                let failed_path = parts[..=i].join(".");
                anyhow!(
                    "設定パス '{}' が見つかりません（'{}'まで到達できました）",
                    path,
                    failed_path
                )
            })?;
        }

        serde_yaml::from_value(current.clone()).with_context(|| {
            format!(
                "設定値の型変換に失敗しました: パス '{path}' の値 '{current:?}'"
            )
        })
    }
}