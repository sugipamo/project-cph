use anyhow::Result;
use crate::config::Config as GlobalConfig;

pub struct CommandResolver {
    config: GlobalConfig,
}

impl CommandResolver {
    pub fn new(config: GlobalConfig) -> Self {
        Self { config }
    }
} 