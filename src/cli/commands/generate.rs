use crate::cli::commands::{Command, Result, CommandContext};
use crate::cli::Commands;
use crate::contest::Contest;
use crate::config::Config;

#[derive(Debug)]
pub struct GenerateCommand {
    context: CommandContext,
}

impl GenerateCommand {
    pub fn new(context: CommandContext) -> Self {
        Self { context }
    }
}

#[async_trait::async_trait]
impl Command for GenerateCommand {
    async fn execute(&self, _command: &Commands, site_id: &str) -> Result<()> {
        // 設定を取得
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストオブジェクトを作成
        let mut contest = Contest::new(&config, &self.context.problem_id)?;
        contest.set_site(site_id)?;

        // テストケースを生成
        contest.generate_test(&self.context.problem_id)?;

        Ok(())
    }
} 