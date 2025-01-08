use crate::config::Config as GlobalConfig;

pub struct CommandResolver {
    #[allow(dead_code)]
    config: GlobalConfig,
}

impl CommandResolver {
    #[must_use = "この関数は新しいCommandResolverインスタンスを返します"]
    pub fn new(config: GlobalConfig) -> Self {
        Self { config }
    }
} 