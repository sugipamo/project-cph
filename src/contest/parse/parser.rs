use anyhow::Result;
use crate::config::Config as GlobalConfig;
use crate::contest::model::CommandContext;
use super::resolver::CommandResolver;

pub struct CommandParser {
    resolver: CommandResolver,
}

impl CommandParser {
    pub fn new(config: &GlobalConfig) -> Result<Self> {
        let resolver = CommandResolver::new(config.clone());
        Ok(Self { resolver })
    }

    pub fn parse(&self, input: &str) -> Result<CommandContext> {
        // TODO: 実際のパース処理を実装
        unimplemented!("parse method is not implemented yet")
    }
} 