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

#[async_trait::async_trait]
impl Command for TestCommand {
    async fn execute(&self, command: &Commands) -> Result<()> {
        let problem_id = match command {
            Commands::Test { problem_id } => problem_id,
            _ => return Err("不正なコマンドです".into()),
        };

        // Note: 現在は同期的な実装のみ
        // TODO: テスト実行の非同期実装
        if let Err(e) = test::run_test(problem_id, self.context.active_contest_dir.clone()) {
            println!("テストの実行に失敗しました: {}", e);
            return Err(e.into());
        }

        Ok(())
    }
} 