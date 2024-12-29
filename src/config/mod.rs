mod commands;
pub mod languages;
mod sites;

pub use commands::CommandConfig;
pub use languages::{LanguageConfig, LanguageInfo};
pub use sites::{SiteConfig, Site};

use std::path::PathBuf;

pub struct ConfigPaths {
    pub commands: PathBuf,
    pub languages: PathBuf,
    pub sites: PathBuf,
}

pub fn get_config_paths() -> ConfigPaths {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    let config_dir = home.join(".config").join("cph");
    
    ConfigPaths {
        commands: config_dir.join("commands.yaml"),
        languages: config_dir.join("languages.yaml"),
        sites: config_dir.join("sites.yaml"),
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
    }
} 