use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::oj::OnlineJudge;

#[derive(Debug)]
pub struct LoginCommand;

impl LoginCommand {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait::async_trait]
impl Command for LoginCommand {
    async fn execute(&self, command: &Commands) -> Result<()> {
        let mut contest = crate::contest::Contest::default();

        // コマンドからsite_idを取得
        if let Commands::Login = command {
            // デフォルトのsite_idを使用
        }

        // OnlineJudgeを初期化
        let mut oj = OnlineJudge::new(&contest);
        oj.login().await?;

        Ok(())
    }
} 