use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::contest::Contest;
use crate::config::Config;
use crate::oj::OnlineJudge;

#[derive(Debug)]
pub struct SubmitCommand {
    problem_id: String,
}

impl SubmitCommand {
    pub fn new(problem_id: String) -> Self {
        Self { problem_id }
    }
}

#[async_trait::async_trait]
impl Command for SubmitCommand {
    async fn execute(&self, command: &Commands) -> Result<()> {
        // 設定を取得
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストオブジェクトを作成
        let mut contest = Contest::new(&config, &self.problem_id)?;

        // OnlineJudgeを初期化
        let mut oj = OnlineJudge::new(&contest);
        oj.submit(&self.problem_id).await?;

        Ok(())
    }
} 