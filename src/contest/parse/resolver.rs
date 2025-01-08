use crate::config::Config as GlobalConfig;

pub struct Resolver {
    #[allow(dead_code)]
    config: GlobalConfig,
}

impl Resolver {
    #[must_use]
    pub const fn new(config: GlobalConfig) -> Self {
        Self { config }
    }
} 