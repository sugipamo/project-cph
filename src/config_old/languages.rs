use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use std::path::{Path, PathBuf};
use crate::docker::runner::command::CompileConfig;

pub const DEFAULT_SOURCE_NAME: &str = "main";
pub const SOURCE_NAME_ENV_KEY: &str = "CPH_SOURCE_NAME";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageConfig {
    pub languages: HashMap<String, LanguageInfo>,
    pub default_language: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageInfo {
    pub aliases: Vec<String>,
    pub extension: String,
    pub template: TemplateConfig,
    pub site_ids: HashMap<String, String>,
    pub runner: RunnerInfo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemplateConfig {
    pub pattern: TemplatePattern,
    pub directory: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemplatePattern {
    pub solution: String,
    pub generator: String,
    pub tester: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerInfo {
    pub image: String,
    pub compile: Option<Vec<String>>,
    pub run: Vec<String>,
    pub compile_dir: String,
}

impl RunnerInfo {
    pub fn needs_compilation(&self) -> bool {
        self.compile.is_some()
    }

    pub fn get_compile_dir(&self) -> &str {
        &self.compile_dir
    }

    pub fn to_compile_config(&self, extension: &str) -> CompileConfig {
        let mut env_vars = Vec::new();
        
        // イメージ名に基づいて環境変数を設定
        if self.image.contains("python") || self.image.contains("pypy") {
            env_vars.push("PYTHONUNBUFFERED=1".to_string());
            env_vars.push("PYTHONIOENCODING=utf-8".to_string());
        }

        CompileConfig {
            extension: extension.to_string(),
            needs_cargo: self.image.starts_with("rust:"),
            env_vars,
        }
    }
}

impl TemplatePattern {
    pub fn resolve(&self, source: &str) -> ResolvedPattern {
        ResolvedPattern {
            solution: self.solution.replace("{source}", source),
            generator: self.generator.replace("{source}", source),
            tester: self.tester.replace("{source}", source),
        }
    }
}

#[derive(Debug, Clone)]
pub struct ResolvedPattern {
    pub solution: String,
    pub generator: String,
    pub tester: String,
}

impl LanguageConfig {
    pub fn load(config_path: PathBuf) -> std::io::Result<Self> {
        if !config_path.exists() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                format!("Language configuration file not found: {}", config_path.display())
            ));
        }

        let content = std::fs::read_to_string(config_path)?;
        let config = serde_yaml::from_str(&content)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
        Ok(config)
    }

    pub fn from_yaml(path: impl AsRef<Path>, language: &str) -> std::io::Result<LanguageInfo> {
        let config = Self::load(path.as_ref().to_path_buf())?;
        config.languages.get(language)
            .cloned()
            .ok_or_else(|| std::io::Error::new(
                std::io::ErrorKind::NotFound,
                format!("Language {} not found", language)
            ))
    }

    pub fn resolve_template_path(&self, language: &str, template_base: impl AsRef<Path>, source: &str) -> Option<PathBuf> {
        let lang_info = self.languages.get(language)?;
        let pattern = lang_info.template.pattern.resolve(source);
        Some(template_base.as_ref()
            .join(&lang_info.template.directory)
            .join(pattern.solution))
    }

    pub fn resolve_language(&self, input: &str) -> Option<String> {
        let input = input.to_lowercase();
        
        // 完全一致の場合はそのまま返す
        if self.languages.contains_key(&input) {
            return Some(input);
        }

        // エイリアスを探索（大文字小文字を区別しない）
        for (lang_name, lang_info) in &self.languages {
            if lang_info.aliases.iter().any(|alias| alias.to_lowercase() == input) {
                return Some(lang_name.clone());
            }
            // 言語名自体も別名として扱う
            if lang_name.to_lowercase() == input {
                return Some(lang_name.clone());
            }
        }

        None
    }

    pub fn get_extension(&self, language: &str) -> Option<String> {
        self.languages.get(language).map(|l| l.extension.clone())
    }

    pub fn get_site_id(&self, language: &str, site: &str) -> Option<String> {
        self.languages.get(language)
            .and_then(|l| l.site_ids.get(site))
            .cloned()
    }

    pub fn get_display_name(&self, language: &str) -> Option<String> {
        self.languages.get(language).map(|_| language.to_string())
    }

    pub fn get_clap_name(&self, language: &str) -> Option<String> {
        self.languages.get(language).map(|_| language.to_string())
    }

    pub fn list_languages(&self) -> Vec<String> {
        self.languages.keys().cloned().collect()
    }

    pub fn get_default_language(&self) -> Option<String> {
        // デフォルト言語が明示的に設定されている場合はそれを返す
        if let Some(default) = &self.default_language {
            if self.languages.contains_key(default) {
                return Some(default.clone());
            }
        }
        // 設定されていない場合は最初の言語を返す（後方互換性のため）
        self.languages.keys().next().cloned()
    }

    pub fn get_language_by_extension(&self, extension: &str) -> Option<String> {
        for (language, info) in &self.languages {
            if info.extension == extension {
                return Some(language.clone());
            }
        }
        None
    }

    pub fn get_template(&self, language: &str, source: &str) -> Option<ResolvedPattern> {
        self.languages.get(language)
            .map(|l| l.template.pattern.resolve(source))
    }
} 