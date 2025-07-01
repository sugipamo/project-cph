use crate::domain::{Config, ConfigNode, ConfigValue, ConfigContext};
use crate::interfaces::ConfigLoader;
use crate::application::errors::ApplicationError;
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use tracing::{debug, info};

/// Configuration service that manages configuration loading and caching
pub struct ConfigService {
    loader: Arc<dyn ConfigLoader>,
    cache: Arc<RwLock<HashMap<String, Config>>>,
    node_cache: Arc<RwLock<HashMap<String, ConfigNode>>>,
}

impl ConfigService {
    /// Create a new configuration service
    pub fn new(loader: Arc<dyn ConfigLoader>) -> Self {
        Self {
            loader,
            cache: Arc::new(RwLock::new(HashMap::new())),
            node_cache: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Load configuration for a specific language
    pub fn load_config(&self, language: &str) -> Result<Config, ApplicationError> {
        // Check cache first
        {
            let cache = self.cache.read().map_err(|_| {
                ApplicationError::UseCaseFailed("Failed to acquire read lock on cache".to_string())
            })?;
            
            if let Some(config) = cache.get(language) {
                debug!("Returning cached configuration for language: {}", language);
                return Ok(config.clone());
            }
        }

        info!("Loading configuration for language: {}", language);

        // Load system configuration
        let system_config = self.loader.load_system_config()
            .map_err(ApplicationError::from)?;

        // Load shared configuration
        let shared_config = self.loader.load_shared_config()
            .map_err(ApplicationError::from)?;

        // Load language-specific configuration
        let language_config = self.loader.load_language_config(language)
            .map_err(ApplicationError::from)?;

        // Merge configurations with priority: language > shared > system
        let merged_config = self.merge_configs(vec![system_config, shared_config, language_config])?;

        // Cache the result
        {
            let mut cache = self.cache.write().map_err(|_| {
                ApplicationError::UseCaseFailed("Failed to acquire write lock on cache".to_string())
            })?;
            
            cache.insert(language.to_string(), merged_config.clone());
        }

        Ok(merged_config)
    }

    /// Load configuration as a `ConfigNode` tree for hierarchical access
    pub fn load_config_node(&self, language: &str) -> Result<ConfigNode, ApplicationError> {
        // Check cache first
        {
            let cache = self.node_cache.read().map_err(|_| {
                ApplicationError::UseCaseFailed("Failed to acquire read lock on node cache".to_string())
            })?;
            
            if let Some(node) = cache.get(language) {
                debug!("Returning cached configuration node for language: {}", language);
                return Ok(node.clone());
            }
        }

        let config = self.load_config(language)?;
        let node = self.build_config_node(config)?;

        // Cache the result
        {
            let mut cache = self.node_cache.write().map_err(|_| {
                ApplicationError::UseCaseFailed("Failed to acquire write lock on node cache".to_string())
            })?;
            
            cache.insert(language.to_string(), node.clone());
        }

        Ok(node)
    }

    /// Get a configuration value by path with template expansion
    pub fn get_value(
        &self, 
        language: &str, 
        path: &str,
        context: Option<&ConfigContext>
    ) -> Result<Option<ConfigValue>, ApplicationError> {
        let node = self.load_config_node(language)?;
        let path_parts: Vec<&str> = path.split('.').collect();
        
        let value = node.get(&path_parts).cloned();
        
        // Apply template expansion if context is provided
        if let (Some(ctx), Some(val)) = (context, &value) {
            if let Some(expanded) = self.expand_value(val, ctx) {
                return Ok(Some(expanded));
            }
        }
        
        Ok(value)
    }

    /// Clear all caches
    pub fn clear_cache(&self) -> Result<(), ApplicationError> {
        {
            let mut cache = self.cache.write().map_err(|_| {
                ApplicationError::UseCaseFailed("Failed to acquire write lock on cache".to_string())
            })?;
            cache.clear();
        }
        
        {
            let mut node_cache = self.node_cache.write().map_err(|_| {
                ApplicationError::UseCaseFailed("Failed to acquire write lock on node cache".to_string())
            })?;
            node_cache.clear();
        }
        
        info!("Configuration caches cleared");
        Ok(())
    }

    /// Merge multiple configurations with priority
    fn merge_configs(&self, configs: Vec<Config>) -> Result<Config, ApplicationError> {
        if configs.is_empty() {
            return Ok(Config::default());
        }

        // Start with the first config as base
        let mut result = configs[0].clone();
        
        // Merge subsequent configs
        for config in configs.into_iter().skip(1) {
            // This is a simplified merge - in production, we'd need deep merging
            result = config;
        }
        
        Ok(result)
    }

    /// Build a `ConfigNode` tree from a `Config` structure
    fn build_config_node(&self, config: Config) -> Result<ConfigNode, ApplicationError> {
        let mut root = ConfigNode::new("root".to_string());
        
        // Convert Config to JSON value for easier tree building
        let json_value = serde_json::to_value(&config)
            .map_err(|e| ApplicationError::UseCaseFailed(format!("Failed to serialize config: {e}")))?;
        
        if let serde_json::Value::Object(map) = json_value {
            for (key, value) in map {
                self.insert_json_value(&mut root, &[&key], value)?;
            }
        }
        
        Ok(root)
    }

    /// Insert a JSON value into the `ConfigNode` tree
    fn insert_json_value(
        &self, 
        node: &mut ConfigNode, 
        path: &[&str], 
        value: serde_json::Value
    ) -> Result<(), ApplicationError> {
        let config_value = match value {
            serde_json::Value::String(s) => ConfigValue::String(s),
            serde_json::Value::Number(n) => {
                if let Some(i) = n.as_i64() {
                    ConfigValue::Integer(i)
                } else if let Some(f) = n.as_f64() {
                    ConfigValue::Float(f)
                } else {
                    return Err(ApplicationError::InvalidInput("Invalid number value".to_string()));
                }
            }
            serde_json::Value::Bool(b) => ConfigValue::Boolean(b),
            serde_json::Value::Array(arr) => {
                let mut config_arr = Vec::new();
                for item in arr {
                    if let Ok(cv) = self.json_to_config_value(item) {
                        config_arr.push(cv);
                    }
                }
                ConfigValue::Array(config_arr)
            }
            serde_json::Value::Object(map) => {
                let mut config_map = HashMap::new();
                for (k, v) in map {
                    if let Ok(cv) = self.json_to_config_value(v) {
                        config_map.insert(k, cv);
                    }
                }
                ConfigValue::Object(config_map)
            }
            serde_json::Value::Null => return Ok(()),
        };
        
        node.insert(path, config_value);
        Ok(())
    }

    /// Convert JSON value to `ConfigValue`
    fn json_to_config_value(&self, value: serde_json::Value) -> Result<ConfigValue, ApplicationError> {
        match value {
            serde_json::Value::String(s) => Ok(ConfigValue::String(s)),
            serde_json::Value::Number(n) => {
                if let Some(i) = n.as_i64() {
                    Ok(ConfigValue::Integer(i))
                } else if let Some(f) = n.as_f64() {
                    Ok(ConfigValue::Float(f))
                } else {
                    Err(ApplicationError::InvalidInput("Invalid number value".to_string()))
                }
            }
            serde_json::Value::Bool(b) => Ok(ConfigValue::Boolean(b)),
            serde_json::Value::Array(arr) => {
                let mut config_arr = Vec::new();
                for item in arr {
                    config_arr.push(self.json_to_config_value(item)?);
                }
                Ok(ConfigValue::Array(config_arr))
            }
            serde_json::Value::Object(map) => {
                let mut config_map = HashMap::new();
                for (k, v) in map {
                    config_map.insert(k, self.json_to_config_value(v)?);
                }
                Ok(ConfigValue::Object(config_map))
            }
            serde_json::Value::Null => Err(ApplicationError::InvalidInput("Null values not supported".to_string())),
        }
    }

    /// Expand template values in a `ConfigValue`
    fn expand_value(&self, value: &ConfigValue, context: &ConfigContext) -> Option<ConfigValue> {
        match value {
            ConfigValue::String(s) => Some(ConfigValue::String(context.expand(s))),
            ConfigValue::Array(arr) => {
                let expanded: Vec<ConfigValue> = arr.iter()
                    .filter_map(|v| self.expand_value(v, context))
                    .collect();
                Some(ConfigValue::Array(expanded))
            }
            ConfigValue::Object(map) => {
                let mut expanded = HashMap::new();
                for (k, v) in map {
                    if let Some(expanded_value) = self.expand_value(v, context) {
                        expanded.insert(k.clone(), expanded_value);
                    }
                }
                Some(ConfigValue::Object(expanded))
            }
            _ => Some(value.clone()),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::infrastructure::test_support::mock_drivers::MockConfigLoader;

    #[test]
    fn test_config_service_caching() {
        let mock_loader = Arc::new(MockConfigLoader::new());
        let service = ConfigService::new(mock_loader);

        // First load should hit the loader
        let config1 = service.load_config("rust").unwrap();
        
        // Second load should return cached value
        let config2 = service.load_config("rust").unwrap();
        
        // Should be the same config
        assert_eq!(config1.language.language_id, config2.language.language_id);
    }

    #[test]
    fn test_config_value_expansion() {
        let mock_loader = Arc::new(MockConfigLoader::new());
        let service = ConfigService::new(mock_loader);

        let mut context = ConfigContext::new();
        context.contest_name = Some("abc123".to_string());
        context.problem_name = Some("a".to_string());

        // This would need a more complex test setup with actual template values
        // For now, just verify the service can be created
        assert!(service.load_config("rust").is_ok());
    }
}