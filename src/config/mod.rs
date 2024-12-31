mod commands;
pub mod languages;
mod sites;
mod oj;
mod merge;
mod docker;

pub use commands::CommandConfig;
pub use languages::{LanguageConfig, LanguageInfo};
pub use sites::{SiteConfig, Site};
pub use oj::OJConfig;
pub use merge::ConfigMerge;
pub use docker::DockerConfig;

use std::path::PathBuf;

pub struct ConfigPaths {
    pub base_dir: PathBuf,
    pub active_dir: PathBuf,

    pub commands: PathBuf,
    pub languages: PathBuf,
    pub sites: PathBuf,
    pub oj: PathBuf,
    pub docker: PathBuf,
}

impl ConfigPaths {
    pub fn get_base_path(&self, file: &PathBuf) -> PathBuf {
        self.base_dir.join(file)
    }

    pub fn get_active_path(&self, file: &PathBuf) -> PathBuf {
        self.active_dir.join(file)
    }

    pub fn get_file_name(&self, file: &PathBuf) -> String {
        file.file_name()
            .and_then(|name| name.to_str())
            .unwrap_or_default()
            .to_string()
    }
}

pub fn get_config_paths() -> ConfigPaths {
    let base_dir = PathBuf::from("src/config");
    let active_dir = PathBuf::from("active_contest");
    
    ConfigPaths {
        commands: PathBuf::from("commands.yaml"),
        languages: PathBuf::from("languages.yaml"),
        sites: PathBuf::from("sites.yaml"),
        oj: PathBuf::from("oj.yaml"),
        docker: PathBuf::from("docker.yaml"),
        base_dir,
        active_dir,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_paths() {
        let paths = get_config_paths();
        
        assert!(paths.base_dir.ends_with("src/config"));
        assert!(paths.active_dir.ends_with("active_contest"));

        assert!(paths.get_base_path(&paths.commands).ends_with("src/config/commands.yaml"));
        assert!(paths.get_base_path(&paths.languages).ends_with("src/config/languages.yaml"));
        assert!(paths.get_base_path(&paths.sites).ends_with("src/config/sites.yaml"));
        assert!(paths.get_base_path(&paths.oj).ends_with("src/config/oj.yaml"));
        assert!(paths.get_base_path(&paths.docker).ends_with("src/config/docker.yaml"));

        assert!(paths.get_active_path(&paths.docker).ends_with("active_contest/docker.yaml"));
    }

    #[test]
    fn test_get_file_name() {
        let paths = get_config_paths();
        assert_eq!(paths.get_file_name(&paths.oj), "oj.yaml");
        assert_eq!(paths.get_file_name(&paths.docker), "docker.yaml");
    }
} 