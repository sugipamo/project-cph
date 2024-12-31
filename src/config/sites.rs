use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use crate::error::Result;
use crate::config::{get_config_paths, merge::ConfigMerge, config_loader::ConfigLoader};

#[derive(Debug, Serialize, Deserialize, Default)]
pub struct SiteConfig {
    #[serde(default)]
    pub sites: HashMap<String, Site>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Site {
    pub name: String,
    pub url: String,
    pub contest_url: Option<String>,
    #[serde(default)]
    pub aliases: Vec<String>,
}

impl ConfigMerge for SiteConfig {
    fn merge(&mut self, other: Self) {
        // サイト設定のマージ
        for (key, value) in other.sites {
            self.sites.insert(key, value);
        }
    }
}

impl ConfigMerge for Site {
    fn merge(&mut self, other: Self) {
        self.name = other.name;
        self.url = other.url;
        self.contest_url = other.contest_url;
        self.aliases = other.aliases;
    }
}

impl ConfigLoader for SiteConfig {}

impl SiteConfig {
    pub fn load() -> Result<Self> {
        let paths = get_config_paths();
        Self::load_with_merge(
            &paths.get_base_path(&paths.sites),
            &paths.get_active_path(&paths.sites),
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
sites:
  atcoder:
    name: "AtCoder"
    url: "https://atcoder.jp"
    contest_url: "https://atcoder.jp/contests/{contest_id}"
    aliases: ["at"]
  codeforces:
    name: "Codeforces"
    url: "https://codeforces.com"
    aliases: ["cf"]
"#;
        create_test_config(&base_dir.join("sites.yaml"), base_content)?;

        // アクティブコンテストの設定を作成
        let active_content = r#"
sites:
  atcoder:
    name: "AtCoder Beta"
    url: "https://atcoder.jp"
    contest_url: "https://beta.atcoder.jp/contests/{contest_id}"
    aliases: ["atc"]
"#;
        create_test_config(&active_dir.join("sites.yaml"), active_content)?;

        // 設定を読み込み
        let config = SiteConfig::load()?;

        // 検証
        let atcoder = config.sites.get("atcoder").unwrap();
        assert_eq!(atcoder.name, "AtCoder Beta");     // 上書きされた値
        assert_eq!(atcoder.aliases, vec!["atc"]);     // 上書きされた値
        assert_eq!(atcoder.contest_url.as_ref().unwrap(), 
                  "https://beta.atcoder.jp/contests/{contest_id}"); // 上書きされた値

        let codeforces = config.sites.get("codeforces").unwrap();
        assert_eq!(codeforces.name, "Codeforces");    // ベース設定の値
        assert_eq!(codeforces.aliases, vec!["cf"]);   // ベース設定の値

        Ok(())
    }
} 