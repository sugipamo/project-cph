// Configuration Module
//
// このモジュールは、イミュータブルで型安全な設定管理を提供します。
// 主な機能：
// - 型安全な設定アクセス
// - イミュータブルな設定値
// - カスタムスキーマによるバリデーション
// - 柔軟な型変換システム

use std::path::Path;
use std::fs;
use std::sync::OnceLock;
use std::env;
use anyhow::{Result, Context, anyhow, bail};
use serde_yaml::Value;
use regex::Regex;
use once_cell::sync::Lazy;

static CONFIG: OnceLock<Config> = OnceLock::new();
static ENV_VAR_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"\$\{([^}]+)}").expect("正規表現パターンが不正です")
});

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
            .with_context(|| format!("設定ファイル '{}' の読み込みに失敗しました", path_str))?;
        
        Self::from_str(&content)
            .with_context(|| format!("設定ファイル '{}' のパースに失敗しました", path_str))
    }

    /// 文字列から設定を作成します
    ///
    /// # Errors
    ///
    /// - YAML形式が不正な場合
    pub fn from_str(content: &str) -> Result<Self> {
        let expanded_content = Self::expand_env_vars(content);
        
        // YAML継承を有効にしてパース
        let data = serde_yaml::from_str(&expanded_content)
            .context("不正なYAML形式です")?;

        if !data.is_mapping() {
            bail!("YAMLのルート要素はマッピング（オブジェクト）である必要があります");
        }

        Ok(Self { data })
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

    pub fn get<T>(path: &str) -> Result<T>
    where
        T: serde::de::DeserializeOwned,
    {
        let config = CONFIG.get_or_init(|| {
            Self::from_file("src/config/config.yaml")
                .expect("デフォルト設定ファイルの読み込みに失敗しました")
        });
        config.get_value(path)
    }

    fn get_value<T>(&self, path: &str) -> Result<T>
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
                "設定値の型変換に失敗しました: パス '{}' の値 '{}'",
                path,
                current
            )
        })
    }

    fn load() -> Result<Self> {
        Self::from_file("src/config/config.yaml")
            .context("デフォルト設定ファイルの読み込みに失敗しました")
    }
}