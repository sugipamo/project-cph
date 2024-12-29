pub mod aliases;

use std::path::{Path, PathBuf};

#[derive(Debug, Clone)]
pub struct ConfigPaths {
    pub aliases: PathBuf,
    pub runner: PathBuf,
}

impl Default for ConfigPaths {
    fn default() -> Self {
        Self {
            aliases: PathBuf::from("src/config/aliases.yaml"),
            runner: PathBuf::from("src/config/runner.yaml"),
        }
    }
}

impl ConfigPaths {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_base_path<P: AsRef<Path>>(base: P) -> Self {
        let base = base.as_ref();
        Self {
            aliases: base.join("config/aliases.yaml"),
            runner: base.join("config/runner.yaml"),
        }
    }
}

pub fn get_config_paths() -> ConfigPaths {
    ConfigPaths::default()
} 