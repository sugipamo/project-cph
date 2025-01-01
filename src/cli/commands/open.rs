use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::contest::Contest;
use crate::config::Config;

#[derive(Debug)]
pub struct OpenCommand {
    problem_id: String,
}

impl OpenCommand {
    pub fn new(problem_id: String) -> Self {
        Self { problem_id }
    }
}

#[async_trait::async_trait]
impl Command for OpenCommand {
    async fn execute(&self, command: &Commands) -> Result<()> {
        // 設定を取得
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストオブジェクトを作成
        let mut contest = Contest::new(&config, &self.problem_id)?;

        // ブラウザで問題を開く
        contest.open_problem(&self.problem_id)?;

        Ok(())
    }
} 