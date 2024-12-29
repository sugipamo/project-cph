use clap::ArgMatches;
use super::{Command, CommandContext, Result};

/// テストコマンド
pub struct TestCommand {
    context: CommandContext,
}

impl TestCommand {
    pub fn new(context: CommandContext) -> Self {
        Self { context }
    }
}

impl Command for TestCommand {
    fn execute(&self, _matches: &ArgMatches) -> Result<()> {
        println!("テストコマンドは開発中です。");
        Ok(())
    }
} 