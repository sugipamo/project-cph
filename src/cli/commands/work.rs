use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::contest::Contest;
use crate::config::Config;

#[derive(Debug)]
pub struct WorkCommand {
    contest_id: String,
}

impl WorkCommand {
    pub fn new(contest_id: String) -> Self {
        Self { contest_id }
    }
}

#[async_trait::async_trait]
impl Command for WorkCommand {
    async fn execute(&self, _command: &Commands, site_id: &str) -> Result<()> {
        // 設定を取得
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストオブジェクトを作成
        let mut contest = Contest::new(&config, &self.contest_id)?;
        contest.set_contest(self.contest_id.clone());
        contest.set_site(site_id)?;

        // コンテストの設定を保存
        contest.save()?;

        Ok(())
    }
} 