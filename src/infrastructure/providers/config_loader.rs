use crate::domain::Config;
use crate::infrastructure::errors::InfrastructureError;
use crate::interfaces::{ConfigLoader, file_system::FileSystem};
use async_trait::async_trait;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tracing::{debug, info};

/// File-based configuration loader implementation
pub struct FileConfigLoader {
    file_system: Arc<dyn FileSystem>,
    base_path: PathBuf,
}

impl FileConfigLoader {
    /// Create a new file-based configuration loader
    pub fn new(file_system: Arc<dyn FileSystem>, base_path: PathBuf) -> Self {
        Self {
            file_system,
            base_path,
        }
    }

    /// Get the path to the configuration directory
    fn get_config_path(&self, subpath: &str) -> PathBuf {
        self.base_path.join("contest_env").join(subpath)
    }

    /// Load configuration from a JSON file asynchronously
    async fn load_json_config_async(&self, path: &Path) -> Result<Config, InfrastructureError> {
        debug!("Loading configuration from: {:?}", path);
        
        let exists = self.file_system.exists(path).await
            .map_err(|e| InfrastructureError::FileSystem(std::io::Error::new(std::io::ErrorKind::Other, e)))?;
            
        if !exists {
            info!("Configuration file not found: {:?}, using defaults", path);
            return Ok(Config::default());
        }

        let content = self.file_system.read(path).await
            .map_err(|e| InfrastructureError::FileSystem(std::io::Error::new(std::io::ErrorKind::Other, e)))?;
        
        serde_json::from_str(&content)
            .map_err(|e| InfrastructureError::Serialization(format!("Failed to parse configuration file: {}", e)))
    }

    /// Merge two configurations, with the second taking priority
    fn merge_configs(&self, _base: Config, overlay: Config) -> Config {
        // For now, we just return the overlay
        // In a real implementation, we'd do deep merging
        overlay
    }
}

#[async_trait]
impl ConfigLoader for FileConfigLoader {
    fn load_system_config(&self) -> Result<Config, InfrastructureError> {
        // System config would typically come from a database or system-wide location
        // For now, we'll use a default configuration
        Ok(Config::default())
    }

    fn load_shared_config(&self) -> Result<Config, InfrastructureError> {
        let path = self.get_config_path("shared/env.json");
        // Use tokio::task::block_in_place to run async code in sync context
        tokio::task::block_in_place(|| {
            tokio::runtime::Handle::current().block_on(self.load_json_config_async(&path))
        })
    }

    fn load_language_config(&self, language: &str) -> Result<Config, InfrastructureError> {
        let path = self.get_config_path(&format!("{}/env.json", language));
        
        // Load shared config as base
        let shared = self.load_shared_config()?;
        
        // Load language-specific config
        let language_config = tokio::task::block_in_place(|| {
            tokio::runtime::Handle::current().block_on(self.load_json_config_async(&path))
        })?;
        
        // Merge configs with language-specific taking priority
        Ok(self.merge_configs(shared, language_config))
    }

    fn load_runtime_config(&self) -> Result<Option<Config>, InfrastructureError> {
        // Runtime config would come from environment variables or command-line args
        // For now, return None
        Ok(None)
    }

    async fn save_config(&self, config: &Config, language: &str) -> Result<(), InfrastructureError> {
        let path = self.get_config_path(&format!("{}/env.json", language));
        
        // Ensure directory exists
        if let Some(parent) = path.parent() {
            self.file_system.create_dir(parent).await
                .map_err(|e| InfrastructureError::FileSystem(std::io::Error::new(std::io::ErrorKind::Other, e)))?;
        }
        
        let content = serde_json::to_string_pretty(config)
            .map_err(|e| InfrastructureError::Serialization(format!("Failed to serialize configuration: {}", e)))?;
        
        self.file_system.write(&path, &content).await
            .map_err(|e| InfrastructureError::FileSystem(std::io::Error::new(std::io::ErrorKind::Other, e)))?;
        
        info!("Configuration saved to: {:?}", path);
        Ok(())
    }
}

/// In-memory configuration loader for testing
pub struct InMemoryConfigLoader {
    configs: std::sync::RwLock<std::collections::HashMap<String, Config>>,
}

impl InMemoryConfigLoader {
    pub fn new() -> Self {
        Self {
            configs: std::sync::RwLock::new(std::collections::HashMap::new()),
        }
    }

    pub fn set_config(&self, key: &str, config: Config) -> Result<(), InfrastructureError> {
        let mut configs = self.configs.write()
            .map_err(|_| InfrastructureError::ConfigurationLoading("Failed to acquire write lock".to_string()))?;
        configs.insert(key.to_string(), config);
        Ok(())
    }
}

#[async_trait]
impl ConfigLoader for InMemoryConfigLoader {
    fn load_system_config(&self) -> Result<Config, InfrastructureError> {
        let configs = self.configs.read()
            .map_err(|_| InfrastructureError::ConfigurationLoading("Failed to acquire read lock".to_string()))?;
        
        Ok(configs.get("system")
            .cloned()
            .unwrap_or_else(Config::default))
    }

    fn load_shared_config(&self) -> Result<Config, InfrastructureError> {
        let configs = self.configs.read()
            .map_err(|_| InfrastructureError::ConfigurationLoading("Failed to acquire read lock".to_string()))?;
        
        Ok(configs.get("shared")
            .cloned()
            .unwrap_or_else(Config::default))
    }

    fn load_language_config(&self, language: &str) -> Result<Config, InfrastructureError> {
        let configs = self.configs.read()
            .map_err(|_| InfrastructureError::ConfigurationLoading("Failed to acquire read lock".to_string()))?;
        
        Ok(configs.get(language)
            .cloned()
            .unwrap_or_else(Config::default))
    }

    fn load_runtime_config(&self) -> Result<Option<Config>, InfrastructureError> {
        let configs = self.configs.read()
            .map_err(|_| InfrastructureError::ConfigurationLoading("Failed to acquire read lock".to_string()))?;
        
        Ok(configs.get("runtime").cloned())
    }

    async fn save_config(&self, config: &Config, language: &str) -> Result<(), InfrastructureError> {
        let mut configs = self.configs.write()
            .map_err(|_| InfrastructureError::ConfigurationLoading("Failed to acquire write lock".to_string()))?;
        configs.insert(language.to_string(), config.clone());
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::infrastructure::drivers::file_system::LocalFileSystem;
    use tempfile::TempDir;

    #[tokio::test(flavor = "multi_thread")]
    async fn test_file_config_loader() {
        let temp_dir = TempDir::new().unwrap();
        let fs = Arc::new(LocalFileSystem::new());
        let loader = FileConfigLoader::new(fs.clone(), temp_dir.path().to_path_buf());

        // Create a test configuration file
        let config_dir = temp_dir.path().join("contest_env/rust");
        fs.create_dir(&config_dir).await.unwrap();
        
        let config_path = config_dir.join("env.json");
        let test_config = Config::default();
        let json = serde_json::to_string_pretty(&test_config).unwrap();
        fs.write(&config_path, &json).await.unwrap();

        // Load the configuration
        let loaded_config = loader.load_language_config("rust").unwrap();
        assert_eq!(loaded_config.language.language_id, test_config.language.language_id);
    }

    #[test]
    fn test_in_memory_config_loader() {
        let loader = InMemoryConfigLoader::new();
        
        let mut config = Config::default();
        config.language.language_id = "test-lang".to_string();
        
        loader.set_config("test", config.clone()).unwrap();
        
        let loaded_config = loader.load_language_config("test").unwrap();
        assert_eq!(loaded_config.language.language_id, "test-lang");
    }
}