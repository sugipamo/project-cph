use std::path::PathBuf;
use crate::error::Result;
use serde::de::DeserializeOwned;
use crate::config::merge::ConfigMerge;

/// 設定ファイルの読み込みと保存を行う共通トレイト
pub trait ConfigLoader: ConfigMerge + DeserializeOwned {
    /// 設定ファイルを読み込む
    fn load_yaml(path: &PathBuf) -> Result<Self> {
        let content = std::fs::read_to_string(path)
            .map_err(|e| format!("Failed to read config file {}: {}", path.display(), e))?;
        
        serde_yaml::from_str(&content)
            .map_err(|e| format!("Failed to parse config file {}: {}", path.display(), e).into())
    }

    /// ベース設定とアクティブコンテストの設定をマージして読み込む
    fn load_with_merge(base_path: &PathBuf, active_path: &PathBuf) -> Result<Self> {
        // ベース設定は必須
        if !base_path.exists() {
            return Err(format!("Base config file not found: {}", base_path.display()).into());
        }

        // ベース設定を読み込み
        let mut config = Self::load_yaml(base_path)?;

        // アクティブコンテストの設定があれば読み込んでマージ
        if active_path.exists() {
            let active_config = Self::load_yaml(active_path)?;
            config.merge(active_config);
        }

        Ok(config)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::{Serialize, Deserialize};
    use std::fs;
    use tempfile::TempDir;

    #[derive(Debug, Serialize, Deserialize, Default)]
    struct TestConfig {
        value: String,
    }

    impl ConfigMerge for TestConfig {
        fn merge(&mut self, other: Self) {
            self.value = other.value;
        }
    }

    impl ConfigLoader for TestConfig {}

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
        let base_path = temp.path().join("base.yaml");
        let active_path = temp.path().join("active.yaml");

        // ベース設定を作成
        create_test_config(&base_path, r#"value: "base""#)?;
        create_test_config(&active_path, r#"value: "active""#)?;

        // 設定を読み込み
        let config = TestConfig::load_with_merge(&base_path, &active_path)?;
        assert_eq!(config.value, "active");

        Ok(())
    }

    #[test]
    fn test_load_base_only() -> Result<()> {
        let temp = TempDir::new()?;
        let base_path = temp.path().join("base.yaml");
        let active_path = temp.path().join("active.yaml");

        // ベース設定のみ作成
        create_test_config(&base_path, r#"value: "base""#)?;

        // 設定を読み込み
        let config = TestConfig::load_with_merge(&base_path, &active_path)?;
        assert_eq!(config.value, "base");

        Ok(())
    }
} 