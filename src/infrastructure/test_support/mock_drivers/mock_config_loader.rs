use crate::domain::Config;
use crate::infrastructure::errors::InfrastructureError;
use crate::interfaces::ConfigLoader;
use async_trait::async_trait;
use std::collections::HashMap;
use std::sync::RwLock;

/// Mock configuration loader for testing
pub struct MockConfigLoader {
    configs: RwLock<HashMap<String, Config>>,
    should_fail: RwLock<bool>,
}

impl MockConfigLoader {
    pub fn new() -> Self {
        let mut configs = HashMap::new();
        configs.insert("system".to_string(), Config::default());
        configs.insert("shared".to_string(), Config::default());
        configs.insert("rust".to_string(), Config::default());
        
        Self {
            configs: RwLock::new(configs),
            should_fail: RwLock::new(false),
        }
    }

    pub fn set_should_fail(&self, should_fail: bool) {
        if let Ok(mut flag) = self.should_fail.write() {
            *flag = should_fail;
        }
    }

    pub fn set_config(&self, key: &str, config: Config) {
        if let Ok(mut configs) = self.configs.write() {
            configs.insert(key.to_string(), config);
        }
    }
}

#[async_trait]
impl ConfigLoader for MockConfigLoader {
    fn load_system_config(&self) -> Result<Config, InfrastructureError> {
        if let Ok(should_fail) = self.should_fail.read() {
            if *should_fail {
                return Err(InfrastructureError::ConfigurationLoading("Mock failure".to_string()));
            }
        }

        let configs = self.configs.read()
            .map_err(|_| InfrastructureError::ConfigurationLoading("Failed to acquire read lock".to_string()))?;
        
        Ok(configs.get("system").cloned().unwrap_or_default())
    }

    fn load_shared_config(&self) -> Result<Config, InfrastructureError> {
        if let Ok(should_fail) = self.should_fail.read() {
            if *should_fail {
                return Err(InfrastructureError::ConfigurationLoading("Mock failure".to_string()));
            }
        }

        let configs = self.configs.read()
            .map_err(|_| InfrastructureError::ConfigurationLoading("Failed to acquire read lock".to_string()))?;
        
        Ok(configs.get("shared").cloned().unwrap_or_default())
    }

    fn load_language_config(&self, language: &str) -> Result<Config, InfrastructureError> {
        if let Ok(should_fail) = self.should_fail.read() {
            if *should_fail {
                return Err(InfrastructureError::ConfigurationLoading("Mock failure".to_string()));
            }
        }

        let configs = self.configs.read()
            .map_err(|_| InfrastructureError::ConfigurationLoading("Failed to acquire read lock".to_string()))?;
        
        Ok(configs.get(language).cloned().unwrap_or_default())
    }

    fn load_runtime_config(&self) -> Result<Option<Config>, InfrastructureError> {
        if let Ok(should_fail) = self.should_fail.read() {
            if *should_fail {
                return Err(InfrastructureError::ConfigurationLoading("Mock failure".to_string()));
            }
        }

        let configs = self.configs.read()
            .map_err(|_| InfrastructureError::ConfigurationLoading("Failed to acquire read lock".to_string()))?;
        
        Ok(configs.get("runtime").cloned())
    }

    async fn save_config(&self, config: &Config, language: &str) -> Result<(), InfrastructureError> {
        if let Ok(should_fail) = self.should_fail.read() {
            if *should_fail {
                return Err(InfrastructureError::ConfigurationLoading("Mock failure".to_string()));
            }
        }

        let mut configs = self.configs.write()
            .map_err(|_| InfrastructureError::ConfigurationLoading("Failed to acquire write lock".to_string()))?;
        
        configs.insert(language.to_string(), config.clone());
        Ok(())
    }
}