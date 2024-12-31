use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use crate::error::Result;
use crate::config::{get_config_paths, merge::ConfigMerge, config_loader::ConfigLoader};

#[derive(Debug, Serialize, Deserialize, Default)]
pub struct DockerConfig {
    #[serde(default)]
    pub images: HashMap<String, ImageConfig>,
    #[serde(default)]
    pub volumes: HashMap<String, VolumeConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ImageConfig {
    pub name: String,
    #[serde(default)]
    pub build_args: HashMap<String, String>,
    #[serde(default)]
    pub env_vars: HashMap<String, String>,
    #[serde(default)]
    pub mounts: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct VolumeConfig {
    pub path: String,
    #[serde(default)]
    pub read_only: bool,
}

impl ConfigMerge for DockerConfig {
    fn merge(&mut self, other: Self) {
        // イメージ設定のマージ
        for (key, value) in other.images {
            self.images.insert(key, value);
        }
        // ボリューム設定のマージ
        for (key, value) in other.volumes {
            self.volumes.insert(key, value);
        }
    }
}

impl ConfigMerge for ImageConfig {
    fn merge(&mut self, other: Self) {
        self.name = other.name;
        // build_argsのマージ（上書き）
        for (key, value) in other.build_args {
            self.build_args.insert(key, value);
        }
        // env_varsのマージ（上書き）
        for (key, value) in other.env_vars {
            self.env_vars.insert(key, value);
        }
        // mountsの置き換え
        self.mounts = other.mounts;
    }
}

impl ConfigMerge for VolumeConfig {
    fn merge(&mut self, other: Self) {
        self.path = other.path;
        self.read_only = other.read_only;
    }
}

impl ConfigLoader for DockerConfig {}

impl DockerConfig {
    pub fn load() -> Result<Self> {
        let paths = get_config_paths();
        Self::load_with_merge(
            &paths.get_base_path(&paths.docker),
            &paths.get_active_path(&paths.docker),
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
images:
  python:
    name: "python:3.9"
    build_args:
      PYTHON_VERSION: "3.9"
    env_vars:
      PYTHONPATH: "/workspace"
    mounts:
      - "workspace:/workspace"
  rust:
    name: "rust:1.70"
    build_args:
      RUST_VERSION: "1.70"
    mounts:
      - "cargo-cache:/usr/local/cargo/registry"

volumes:
  workspace:
    path: "/workspace"
    read_only: false
  cargo-cache:
    path: "/usr/local/cargo/registry"
    read_only: false
"#;
        create_test_config(&base_dir.join("docker.yaml"), base_content)?;

        // アクティブコンテストの設定を作成
        let active_content = r#"
images:
  python:
    name: "python:3.11"
    build_args:
      PYTHON_VERSION: "3.11"
    env_vars:
      PYTHONPATH: "/workspace/lib"
      PYTHONUNBUFFERED: "1"
    mounts:
      - "workspace:/workspace"
      - "pip-cache:/root/.cache/pip"
"#;
        create_test_config(&active_dir.join("docker.yaml"), active_content)?;

        // 設定を読み込み
        let config = DockerConfig::load()?;

        // Python設定の検証
        let python = config.images.get("python").unwrap();
        assert_eq!(python.name, "python:3.11");                    // 上書きされた値
        assert_eq!(python.build_args.get("PYTHON_VERSION").unwrap(), "3.11"); // 上書きされた値
        assert_eq!(python.env_vars.get("PYTHONPATH").unwrap(), "/workspace/lib"); // 上書きされた値
        assert_eq!(python.env_vars.get("PYTHONUNBUFFERED").unwrap(), "1"); // 追加された値
        assert_eq!(python.mounts.len(), 2);                       // 上書きされた値

        // Rust設定の検証（変更なし）
        let rust = config.images.get("rust").unwrap();
        assert_eq!(rust.name, "rust:1.70");                       // ベース設定の値
        assert_eq!(rust.build_args.get("RUST_VERSION").unwrap(), "1.70"); // ベース設定の値

        // ボリューム設定の検証（変更なし）
        let workspace = config.volumes.get("workspace").unwrap();
        assert_eq!(workspace.path, "/workspace");                 // ベース設定の値
        assert_eq!(workspace.read_only, false);                   // ベース設定の値

        Ok(())
    }
} 