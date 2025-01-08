use anyhow::Result;
use crate::contest::model::CommandContext;

pub struct Parser;

impl Parser {
    pub fn new() -> Self {
        Self
    }

    pub fn parse(&self, _input: &str) -> Result<CommandContext> {
        // TODO: 実装
        unimplemented!()
    }
} 