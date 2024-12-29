use super::{Command, Result, CommandContext};
use crate::cli::Commands;
use crate::test;

pub struct TestCommand {
    context: CommandContext,
}

impl TestCommand {
    pub fn new(context: CommandContext) -> Self {
        Self { context }
    }
}

impl Command for TestCommand {
    fn execute(&self, command: &Commands) -> Result<()> {
        let problem_id = match command {
            Commands::Test { problem_id } => problem_id,
            _ => return Err("不正なコマンドです".into()),
        };

        test::run_test(problem_id, self.context.workspace_path.clone())?;
        Ok(())
    }
} 