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
use std::env;
use regex::Regex;
use once_cell::sync::Lazy;
use yaml_rust::{YamlLoader, Yaml};
use yaml_rust::yaml::Hash;

static ENV_VAR_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"\$\{([^}]+)}").expect("正規表現パターンが不正です")
});

#[derive(Debug, Clone)]
pub struct Config {
    data: Value,
}

#[derive(Debug, Clone)]
pub struct ConfigValue {
    data: Value,
}

impl ConfigValue {
    fn new(data: Value) -> Self {
        Self { data }
    }

    /// 設定値を取得します
    ///
    /// # Arguments
    ///
    /// * `path` - ドット区切りの設定パス
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
        Config::convert_value(&self.data, path)
    }

    /// 設定のセクションを取得します
    ///
    /// # Arguments
    ///
    /// * `path` - ドット区切りの設定パス
    ///
    /// # Returns
    ///
    /// * `Result<ConfigValue>` - 設定のセクション
    ///
    /// # Errors
    ///
    /// - 設定パスが存在しない場合
    pub fn get_section(&self, path: &str) -> Result<ConfigValue> {
        let mut current_value = &self.data;
        let mut current_path = String::new();

        for part in path.split('.') {
            if !current_path.is_empty() {
                current_path.push('.');
            }
            current_path.push_str(part);

            if let Some((array_path, index)) = Config::parse_array_access(part) {
                if !array_path.is_empty() {
                    match current_value {
                        Value::Mapping(map) => {
                            current_value = map.get(Value::String(array_path.to_string()))
                                .ok_or_else(|| anyhow!("設定パス '{}' が見つかりません", current_path))?;
                        }
                        _ => {
                            return Err(anyhow!("設定パス '{}' が見つかりません", current_path));
                        }
                    }
                }

                match current_value {
                    Value::Sequence(array) => {
                        current_value = array.get(index)
                            .ok_or_else(|| anyhow!("配列のインデックス {} が範囲外です（パス: '{}'）", index, current_path))?;
                    }
                    _ => {
                        return Err(anyhow!("パス '{}' は配列ではありません", current_path));
                    }
                }
            } else {
                match current_value {
                    Value::Mapping(map) => {
                        current_value = map.get(Value::String(part.to_string()))
                            .ok_or_else(|| anyhow!("設定パス '{}' が見つかりません", current_path))?;
                    }
                    _ => {
                        return Err(anyhow!("設定パス '{}' が見つかりません", current_path));
                    }
                }
            }
        }

        Ok(ConfigValue::new(current_value.clone()))
    }
}

impl Config {
    /// デフォルトの設定ファイルから設定を読み込みます
    ///
    /// # Returns
    ///
    /// * `Result<Self>` - 読み込まれた設定
    ///
    /// # Errors
    ///
    /// - 設定ファイルが存在しない場合
    /// - 設定ファイルの形式が不正な場合
    pub fn default() -> Result<Self> {
        Self::from_file("src/config/config.yaml")
    }

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
                
                // 上書きと深いマージ
                for (key, value) in hash {
                    if key != &Yaml::String("<<".to_string()) {
                        match (result.get(key), value) {
                            // 両方がハッシュの場合は再帰的にマージ
                            (Some(Yaml::Hash(existing)), Yaml::Hash(new)) => {
                                let mut merged = existing.clone();
                                for (k, v) in new {
                                    match (merged.get(k), v) {
                                        (Some(Yaml::Hash(e)), Yaml::Hash(n)) => {
                                            let mut deep_merged = e.clone();
                                            for (dk, dv) in n {
                                                deep_merged.insert(dk.clone(), Self::process_yaml(dv)?);
                                            }
                                            merged.insert(k.clone(), Yaml::Hash(deep_merged));
                                        }
                                        _ => {
                                            merged.insert(k.clone(), Self::process_yaml(v)?);
                                        }
                                    }
                                }
                                result.insert(key.clone(), Yaml::Hash(merged));
                            }
                            // それ以外の場合は単純に上書き
                            _ => {
                                result.insert(key.clone(), Self::process_yaml(value)?);
                            }
                        }
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
    /// ネストされた環境変数（${VAR1-${VAR2-default}}）もサポート
    fn expand_env_vars(content: &str) -> String {
        let mut result = content.to_string();
        let mut prev_result = String::new();
        
        // 環境変数が完全に展開されるまで繰り返す
        while result != prev_result {
            prev_result.clone_from(&result);
            result = ENV_VAR_PATTERN.replace_all(&prev_result, |caps: &regex::Captures| {
                let var_spec = &caps[1];
                Self::expand_var_spec(var_spec)
            }).to_string();
        }
        
        result
    }

    /// 環境変数指定を展開します
    fn expand_var_spec(var_spec: &str) -> String {
        if let Some((var_name, default)) = var_spec.split_once('-') {
            // デフォルト値に環境変数が含まれている場合は再帰的に展開
            if default.contains("${") {
                env::var(var_name).unwrap_or_else(|_| Self::expand_env_vars(default))
            } else {
                env::var(var_name).unwrap_or_else(|_| default.to_string())
            }
        } else {
            env::var(var_spec).unwrap_or_default()
        }
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
    pub fn get_default<T>(path: &str) -> Result<T>
    where
        T: serde::de::DeserializeOwned,
    {
        let config = Self::default()?;
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
        let mut current_value = &self.data;
        let mut current_path = String::new();

        for part in path.split('.') {
            if !current_path.is_empty() {
                current_path.push('.');
            }
            current_path.push_str(part);

            // 配列アクセスの処理
            if let Some((array_path, index)) = Self::parse_array_access(part) {
                // 配列パスの部分を処理
                if !array_path.is_empty() {
                    match current_value {
                        Value::Mapping(map) => {
                            current_value = map.get(Value::String(array_path.to_string()))
                                .ok_or_else(|| anyhow!("設定パス '{}' が見つかりません", current_path))?;
                        }
                        _ => {
                            return Err(anyhow!("設定パス '{}' が見つかりません", current_path));
                        }
                    }
                }

                // 配列のインデックスアクセス
                match current_value {
                    Value::Sequence(array) => {
                        current_value = array.get(index)
                            .ok_or_else(|| anyhow!("配列のインデックス {} が範囲外です（パス: '{}'）", index, current_path))?;
                    }
                    _ => {
                        return Err(anyhow!("パス '{}' は配列ではありません", current_path));
                    }
                }
            } else {
                // 通常のパスアクセス
                match current_value {
                    Value::Mapping(map) => {
                        current_value = map.get(Value::String(part.to_string()))
                            .ok_or_else(|| anyhow!("設定パス '{}' が見つかりません", current_path))?;
                    }
                    _ => {
                        return Err(anyhow!("設定パス '{}' が見つかりません", current_path));
                    }
                }
            }
        }

        Self::convert_value(current_value, path)
    }

    /// 配列アクセスのパターンを解析します
    /// 例: "array[0]" -> ("array", 0)
    fn parse_array_access(part: &str) -> Option<(&str, usize)> {
        if let Some(bracket_pos) = part.find('[') {
            if part.ends_with(']') {
                let array_path = &part[..bracket_pos];
                let index_str = &part[bracket_pos + 1..part.len() - 1];
                if let Ok(index) = index_str.parse::<usize>() {
                    return Some((array_path, index));
                }
            }
        }
        None
    }

    /// 設定値を型変換します
    ///
    /// # Arguments
    ///
    /// * `value` - 変換する値
    /// * `path` - 設定パス（エラーメッセージ用）
    ///
    /// # Returns
    ///
    /// * `Result<T>` - 変換された値
    ///
    /// # Errors
    ///
    /// - 型変換に失敗した場合
    fn convert_value<T>(value: &Value, path: &str) -> Result<T>
    where
        T: serde::de::DeserializeOwned,
    {
        // 直接の変換を試みる
        if let Ok(converted) = serde_yaml::from_value(value.clone()) {
            return Ok(converted);
        }

        // 文字列からの変換を試みる
        if let Value::String(s) = value {
            // 数値への変換
            if std::any::type_name::<T>() == std::any::type_name::<i64>() {
                if let Ok(num) = s.parse::<i64>() {
                    if let Ok(converted) = serde_yaml::from_value(Value::Number(serde_yaml::Number::from(num))) {
                        return Ok(converted);
                    }
                }
            }
            // 浮動小数点数への変換
            if std::any::type_name::<T>() == std::any::type_name::<f64>() {
                if let Ok(num) = s.parse::<f64>() {
                    #[allow(clippy::cast_possible_truncation)]
                    let value = Value::Number(serde_yaml::Number::from(num as i64));
                    if let Ok(converted) = serde_yaml::from_value(value) {
                        return Ok(converted);
                    }
                }
            }
            // ブール値への変換
            if std::any::type_name::<T>() == std::any::type_name::<bool>() {
                let lower = s.to_lowercase();
                if lower == "true" || lower == "yes" || lower == "1" {
                    if let Ok(converted) = serde_yaml::from_value(Value::Bool(true)) {
                        return Ok(converted);
                    }
                } else if lower == "false" || lower == "no" || lower == "0" {
                    if let Ok(converted) = serde_yaml::from_value(Value::Bool(false)) {
                        return Ok(converted);
                    }
                }
            }
        }

        // 数値型の特別な処理
        if let Value::Number(num) = value {
            if std::any::type_name::<T>() == std::any::type_name::<i64>() && num.is_f64() {
                #[allow(clippy::cast_possible_truncation)]
                let value = Value::Number(serde_yaml::Number::from(num.as_f64()
                    .expect("数値が浮動小数点数として解釈できません") as i64));
                if let Ok(converted) = serde_yaml::from_value(value) {
                    return Ok(converted);
                }
            }
        }

        // 変換に失敗した場合
        Err(anyhow!("設定値 '{path}' の型変換に失敗しました"))
    }

    /// 設定のセクションを取得します
    ///
    /// # Arguments
    ///
    /// * `path` - ドット区切りの設定パス
    ///
    /// # Returns
    ///
    /// * `Result<ConfigValue>` - 設定のセクション
    ///
    /// # Errors
    ///
    /// - 設定パスが存在しない場合
    pub fn get_section(&self, path: &str) -> Result<ConfigValue> {
        let mut current_value = &self.data;
        let mut current_path = String::new();

        for part in path.split('.') {
            if !current_path.is_empty() {
                current_path.push('.');
            }
            current_path.push_str(part);

            if let Some((array_path, index)) = Self::parse_array_access(part) {
                if !array_path.is_empty() {
                    match current_value {
                        Value::Mapping(map) => {
                            current_value = map.get(Value::String(array_path.to_string()))
                                .ok_or_else(|| anyhow!("設定パス '{}' が見つかりません", current_path))?;
                        }
                        _ => {
                            return Err(anyhow!("設定パス '{}' が見つかりません", current_path));
                        }
                    }
                }

                match current_value {
                    Value::Sequence(array) => {
                        current_value = array.get(index)
                            .ok_or_else(|| anyhow!("配列のインデックス {} が範囲外です（パス: '{}'）", index, current_path))?;
                    }
                    _ => {
                        return Err(anyhow!("パス '{}' は配列ではありません", current_path));
                    }
                }
            } else {
                match current_value {
                    Value::Mapping(map) => {
                        current_value = map.get(Value::String(part.to_string()))
                            .ok_or_else(|| anyhow!("設定パス '{}' が見つかりません", current_path))?;
                    }
                    _ => {
                        return Err(anyhow!("設定パス '{}' が見つかりません", current_path));
                    }
                }
            }
        }

        Ok(ConfigValue::new(current_value.clone()))
    }
}