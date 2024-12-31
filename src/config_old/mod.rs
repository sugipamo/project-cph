mod commands;
pub mod languages;
mod sites;
mod oj;

pub use commands::CommandConfig;
pub use languages::{LanguageConfig, LanguageInfo};
pub use sites::{SiteConfig, Site};
pub use oj::OJConfig;

use std::path::PathBuf;

pub struct ConfigPaths {
    pub commands: PathBuf,
    pub languages: PathBuf,
    pub sites: PathBuf,
    pub oj: PathBuf,
}

pub fn get_config_paths() -> ConfigPaths {
    let config_dir = PathBuf::from("src/config");
    
    ConfigPaths {
        commands: config_dir.join("commands.yaml"),
        languages: config_dir.join("languages.yaml"),
        sites: config_dir.join("sites.yaml"),
        oj: config_dir.join("oj.yaml"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_paths() {
        let paths = get_config_paths();
        assert!(paths.commands.ends_with("commands.yaml"));
        assert!(paths.languages.ends_with("languages.yaml"));
        assert!(paths.sites.ends_with("sites.yaml"));
        assert!(paths.oj.ends_with("oj.yaml"));
    }
} 