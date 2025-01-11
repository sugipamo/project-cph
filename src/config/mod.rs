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
use std::collections::HashMap;
use anyhow::{Result, Context};
use serde::{Deserialize, Serialize};

#[allow(clippy::module_name_repetitions)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub system: SystemConfig,
    pub languages: LanguagesConfig,
}

#[allow(clippy::module_name_repetitions)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemConfig {
    pub browser: String,
    pub editors: Vec<String>,
    pub docker: DockerConfig,
}

#[allow(clippy::module_name_repetitions)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DockerConfig {
    pub timeout_seconds: u32,
    pub memory_limit_mb: u32,
    pub mount_point: String,
}

#[allow(clippy::module_name_repetitions)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguagesConfig {
    pub default: String,
    #[serde(rename = "_base")]
    pub base: LanguageBaseConfig,
}

#[allow(clippy::module_name_repetitions)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageBaseConfig {
    pub compile: Vec<String>,
    pub run: Vec<String>,
    pub runner: RunnerConfig,
    pub templates: TemplatesConfig,
    pub contest_dir: ContestDirConfig,
    pub active_contest_yaml: String,
    pub test: TestConfig,
}

#[allow(clippy::module_name_repetitions)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerConfig {
    pub compile_dir: String,
    pub require_files: Vec<String>,
    pub env_vars: Vec<String>,
    pub docker: DockerConfig,
}

#[allow(clippy::module_name_repetitions)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemplatesConfig {
    pub patterns: HashMap<String, String>,
    pub directory: String,
}

#[allow(clippy::module_name_repetitions)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContestDirConfig {
    pub active: String,
    pub storage: String,
    pub template: String,
}

#[allow(clippy::module_name_repetitions)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestConfig {
    pub dir: String,
}

impl Config {
    /// 設定ファイルから設定を読み込みます
    /// 
    /// # Errors
    /// 
    /// - 設定ファイルが存在しない場合
    /// - 設定ファイルの形式が不正な場合
    pub fn load() -> Result<Self> {
        let config_path = Path::new("src/config/config.yaml");
        let config_str = fs::read_to_string(config_path)
            .with_context(|| format!("設定ファイルの読み込みに失敗: {}", config_path.display()))?;
        let config: Self = serde_yaml::from_str(&config_str)
            .with_context(|| "設定ファイルのパースに失敗")?;
        Ok(config)
    }

    /// ブラウザの設定を取得します
    #[must_use]
    pub fn browser(&self) -> &str {
        &self.system.browser
    }

    /// エディタの設定を取得します
    #[must_use]
    pub fn editors(&self) -> &[String] {
        &self.system.editors
    }

    /// Dockerの設定を取得します
    #[must_use]
    pub const fn docker(&self) -> &DockerConfig {
        &self.system.docker
    }

    /// デフォルトの言語を取得します
    #[must_use]
    pub fn default_language(&self) -> &str {
        &self.languages.default
    }

    /// テストディレクトリを取得します
    #[must_use]
    pub fn test_dir(&self) -> String {
        self.languages.base.test.dir.clone()
    }

    /// アクティブなコンテストのディレクトリを取得します
    #[must_use]
    pub fn active_contest_dir(&self) -> String {
        self.languages.base.contest_dir.active.clone()
    }

    /// コンテストのテンプレートディレクトリを取得します
    #[must_use]
    pub fn contest_template_dir(&self) -> String {
        self.languages.base.contest_dir.template.clone()
    }

    /// コンテストのストレージディレクトリを取得します
    #[must_use]
    pub fn contest_storage_dir(&self) -> String {
        self.languages.base.contest_dir.storage.clone()
    }

    /// 指定された言語の設定を取得します
    pub fn get_language_config(&self, language: &str) -> Result<&LanguageConfig> {
        self.languages.get(language)
            .ok_or_else(|| anyhow::anyhow!("言語の設定が見つかりません: {}", language))
    }

    /// 指定された言語のDockerイメージを取得します
    pub fn get_language_image(&self, language: &str) -> Result<String> {
        let lang_config = self.get_language_config(language)?;
        Ok(lang_config.runner.image.clone())
    }

    /// 指定された言語のコンパイルコマンドを取得します
    pub fn get_language_compile_command(&self, language: &str) -> Result<Vec<String>> {
        let lang_config = self.get_language_config(language)?;
        Ok(lang_config.compile.clone())
    }

    /// 指定された言語の実行コマンドを取得します
    pub fn get_language_run_command(&self, language: &str) -> Result<Vec<String>> {
        let lang_config = self.get_language_config(language)?;
        Ok(lang_config.run.clone())
    }

    /// 指定された言語の環境変数を取得します
    pub fn get_language_env_vars(&self, language: &str) -> Result<Vec<String>> {
        let lang_config = self.get_language_config(language)?;
        Ok(lang_config.runner.env_vars.clone())
    }

    /// 指定された言語のDocker設定を取得します
    pub fn get_language_docker_config(&self, language: &str) -> Result<&DockerConfig> {
        let lang_config = self.get_language_config(language)?;
        Ok(&lang_config.runner.docker)
    }
}

// 言語固有の設定を表す構造体を追加
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageConfig {
    pub extension: String,
    pub runner: RunnerConfig,
    pub compile: Vec<String>,
    pub run: Vec<String>,
    #[serde(default)]
    pub site_ids: HashMap<String, String>,
} 