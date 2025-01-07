use crate::config::Config as GlobalConfig;

pub struct CommandResolver {
    #[allow(dead_code)]
    config: GlobalConfig,
}

impl CommandResolver {
    pub fn new(config: GlobalConfig) -> Self {
        Self { config }
    }
} 