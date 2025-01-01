use super::{Command, Result};
use crate::cli::Commands;
use crate::oj::OJContainer;
use crate::contest::Contest;
use crate::config::Config;

pub struct LoginCommand {
    site_id: String,
}

impl LoginCommand {
    pub fn new(site_id: String) -> Self {
        Self { site_id }
    }
}

#[async_trait::async_trait]
impl Command for LoginCommand {
    async fn execute(&self, command: &Commands) -> Result<()> {
        match command {
            Commands::Login => (),
            _ => return Err("不正なコマンドです".into()),
        }

        // 設定を取得
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストオブジェクトを作成
        let mut contest = Contest::default();
        contest.set_site(&self.site_id)?;

        // ワークスペースディレクトリを取得
        let workspace_path = std::env::current_dir()?;

        // OJコンテナを初期化
        let oj = OJContainer::new(workspace_path, contest)?;

        // コンテナイメージの確認
        if let Err(e) = oj.ensure_image().await {
            println!("コンテナイメージの確認に失敗しました: {}", e);
            return Err(e.into());
        }
        
        // ログイン処理
        match oj.login().await {
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