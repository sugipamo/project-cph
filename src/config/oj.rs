use serde::{Serialize, Deserialize};
use std::path::PathBuf;
use crate::error::Result;
use crate::config::{get_config_paths, merge::ConfigMerge, config_loader::ConfigLoader};

#[derive(Debug, Serialize, Deserialize, Default)]
pub struct OJConfig {
    #[serde(default)]
    pub submit: SubmitConfig,
    #[serde(default)]
    pub test: TestConfig,
}

#[derive(Debug, Serialize, Deserialize, Default)]
pub struct SubmitConfig {
    #[serde(default = "default_wait")]
    pub wait: u32,
    #[serde(default = "default_auto_yes")]
    pub auto_yes: bool,
}

#[derive(Debug, Serialize, Deserialize, Default)]
pub struct TestConfig {
    #[serde(default = "default_test_directory")]
    pub directory: String,
}

// デフォルト値を提供する関数
fn default_wait() -> u32 { 0 }
fn default_auto_yes() -> bool { true }
fn default_test_directory() -> String { "test".to_string() }

impl ConfigMerge for OJConfig {
    fn merge(&mut self, other: Self) {
        self.submit.merge(other.submit);
        self.test.merge(other.test);
    }
}

impl ConfigMerge for SubmitConfig {
    fn merge(&mut self, other: Self) {
        self.wait.merge(other.wait);
        self.auto_yes.merge(other.auto_yes);
    }
}

impl ConfigMerge for TestConfig {
    fn merge(&mut self, other: Self) {
        self.directory.merge(other.directory);
    }
}

impl ConfigLoader for OJConfig {}

impl OJConfig {
    pub fn load() -> Result<Self> {
        let paths = get_config_paths();
        Self::load_with_merge(
            &paths.get_base_path(&paths.oj),
            &paths.get_active_path(&paths.oj),
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
submit:
  wait: 0
  auto_yes: false
test:
  directory: "test"
"#;
        create_test_config(&base_dir.join("oj.yaml"), base_content)?;

        // アクティブコンテストの設定を作成
        let active_content = r#"
submit:
  wait: 10
"#;
        create_test_config(&active_dir.join("oj.yaml"), active_content)?;

        // 設定を読み込み
        let config = OJConfig::load()?;

        // 検証
        assert_eq!(config.submit.wait, 10);        // アクティブコンテストの値
        assert_eq!(config.submit.auto_yes, false); // ベース設定の値
        assert_eq!(config.test.directory, "test"); // ベース設定の値

        Ok(())
    }
} 