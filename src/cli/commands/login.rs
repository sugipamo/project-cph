use super::{Command, Result, CommandContext};
use crate::cli::Commands;
use crate::oj::OJContainer;

pub struct LoginCommand {
    context: CommandContext,
}

impl LoginCommand {
    pub fn new(context: CommandContext) -> Self {
        Self { context }
    }
}

impl Command for LoginCommand {
    fn execute(&self, command: &Commands) -> Result<()> {
        match command {
            Commands::Login => (),
            _ => return Err("不正なコマンドです".into()),
        }

        // OJコンテナを初期化
        let oj = OJContainer::new(self.context.active_contest_dir.clone())?;

        // ログインを実行
        tokio::runtime::Runtime::new()?.block_on(async {
            // コンテナイメージの確認
            oj.ensure_image().await?;
            
            // ログイン処理
            oj.login(&self.context.site).await.map_err(|e| e.into())
        })
    }
} 