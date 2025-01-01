use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::oj::OJContainer;

#[derive(Debug)]
pub struct LoginCommand;

impl LoginCommand {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait::async_trait]
impl Command for LoginCommand {
    async fn execute(&self, _command: &Commands, site_id: &str) -> Result<()> {
        let mut contest = crate::contest::Contest::default();
        contest.set_site(site_id)?;

        // ワークスペースディレクトリを取得
        let workspace_path = std::env::current_dir()?;

        // OJコンテナを初期化
        let oj = OJContainer::new(workspace_path, contest)?;
        oj.login().await?;

        Ok(())
    }
} 