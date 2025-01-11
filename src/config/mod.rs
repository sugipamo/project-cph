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
use anyhow::{Result, Context, anyhow, bail};
use serde_yaml::Value;

#[derive(Debug)]
pub struct ConfigError {
    path: String,
    message: String,
}

static CONFIG: OnceLock<Config> = OnceLock::new();

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
        let data: Value = serde_yaml::from_str(content)
            .context("不正なYAML形式です")?;

        if !data.is_mapping() {
            bail!("YAMLのルート要素はマッピング（オブジェクト）である必要があります");
        }

        Ok(Self { data })
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