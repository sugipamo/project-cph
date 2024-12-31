use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use crate::error::Result;
use crate::config::{get_config_paths, merge::ConfigMerge, config_loader::ConfigLoader};

#[derive(Debug, Serialize, Deserialize, Default)]
pub struct LanguageConfig {
    #[serde(default)]
    pub languages: HashMap<String, LanguageInfo>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageInfo {
    pub name: String,
    pub extension: String,
    pub template: Option<String>,
    #[serde(default)]
    pub aliases: Vec<String>,
    pub oj_id: Option<String>,
}

impl ConfigMerge for LanguageConfig {
    fn merge(&mut self, other: Self) {
        // 言語設定のマージ
        for (key, value) in other.languages {
            self.languages.insert(key, value);
        }
    }
}

impl ConfigMerge for LanguageInfo {
    fn merge(&mut self, other: Self) {
        self.name = other.name;
        self.extension = other.extension;
        self.template = other.template;
        self.aliases = other.aliases;
        self.oj_id = other.oj_id;
    }
}

impl ConfigLoader for LanguageConfig {}

impl LanguageConfig {
    pub fn load() -> Result<Self> {
        let paths = get_config_paths();
        Self::load_with_merge(
            &paths.get_base_path(&paths.languages),
            &paths.get_active_path(&paths.languages),
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    fn create_test_config(dir: &PathBuf, content: &str) -> Result<()> {
        if let Some(parent) = dir.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::write(dir, content)?;
        Ok(())
    }

    #[test]
    fn test_load_with_merge() -> Result<()> {
        let temp = TempDir::new()?;
        let base_dir = temp.path().join("src/config");
        let active_dir = temp.path().join("active_contest");

        // ベース設定を作成
        let base_content = r#"
languages:
  python:
    name: "Python"
    extension: "py"
    template: "template.py"
    aliases: ["py", "python3"]
    oj_id: "4006"
  rust:
    name: "Rust"
    extension: "rs"
    aliases: ["rs"]
    oj_id: "4050"
"#;
        create_test_config(&base_dir.join("languages.yaml"), base_content)?;

        // アクティブコンテストの設定を作成
        let active_content = r#"
languages:
  python:
    name: "Python 3"
    extension: "py"
    template: "custom_template.py"
    aliases: ["py3"]
    oj_id: "4006"
"#;
        create_test_config(&active_dir.join("languages.yaml"), active_content)?;

        // 設定を読み込み
        let config = LanguageConfig::load()?;

        // 検証
        let python = config.languages.get("python").unwrap();
        assert_eq!(python.name, "Python 3");           // 上書きされた値
        assert_eq!(python.template.as_ref().unwrap(), "custom_template.py"); // 上書きされた値
        assert_eq!(python.aliases, vec!["py3"]);       // 上書きされた値

        let rust = config.languages.get("rust").unwrap();
        assert_eq!(rust.name, "Rust");                 // ベース設定の値
        assert_eq!(rust.extension, "rs");              // ベース設定の値

        Ok(())
    }
} 