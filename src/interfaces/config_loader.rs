use crate::domain::Config;
use crate::infrastructure::errors::InfrastructureError;
use async_trait::async_trait;

/// Interface for loading configuration from various sources
#[async_trait]
pub trait ConfigLoader: Send + Sync {
    /// Load system-wide configuration
    fn load_system_config(&self) -> Result<Config, InfrastructureError>;
    
    /// Load shared configuration across all languages
    fn load_shared_config(&self) -> Result<Config, InfrastructureError>;
    
    /// Load language-specific configuration
    fn load_language_config(&self, language: &str) -> Result<Config, InfrastructureError>;
    
    /// Load runtime configuration overlay
    fn load_runtime_config(&self) -> Result<Option<Config>, InfrastructureError>;
    
    /// Save configuration
    async fn save_config(&self, config: &Config, language: &str) -> Result<(), InfrastructureError>;
}