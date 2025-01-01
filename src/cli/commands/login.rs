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

#[async_trait::async_trait]
impl Command for LoginCommand {
    async fn execute(&self, command: &Commands) -> Result<()> {
        match command {
            Commands::Login => (),
            _ => return Err("不正なコマンドです".into()),
        }

        // ワークスペースディレクトリを取得
        let workspace_path = std::env::current_dir()?;

        // OJコンテナを初期化
        let oj = OJContainer::new(workspace_path)?;

        // コンテナイメージの確認
        if let Err(e) = oj.ensure_image().await {
            println!("コンテナイメージの確認に失敗しました: {}", e);
            return Err(e.into());
        }
        
        // ログイン処理
        match oj.login(&self.context.site).await {
            Ok(_) => {
                println!("ログインが完了しました");
                Ok(())
            },
            Err(e) => {
                println!("ログインに失敗しました: {}", e);
                // ログインの失敗は重大なエラーとして扱う
                Err(e.into())
            }
        }
    }
} 