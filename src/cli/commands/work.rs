use crate::cli::Site;
use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::contest::Contest;
use crate::config::Config;

pub struct WorkCommand {
    pub site: Site,
    pub problem_id: String,
}

impl WorkCommand {
    pub fn new(site: Site, problem_id: String) -> Self {
        Self { site, problem_id }
    }
}

#[async_trait::async_trait]
impl Command for WorkCommand {
    async fn execute(&self, command: &Commands) -> Result<()> {
        let contest_id = match command {
            Commands::Work { contest_id } => contest_id,
            _ => return Err("不正なコマンドです".into()),
        };

        // 設定を取得
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストを読み込む
        let mut contest = Contest::new(&config, contest_id)?;
        
        // サイトを設定
        if let Err(e) = contest.set_site(&self.site.to_string()) {
            println!("サイトの設定に失敗しました: {}", e);
            return Err(e.into());
        }

        // コンテストを保存
        if let Err(e) = contest.save() {
            println!("コンテストの保存に失敗しました: {}", e);
            return Err(e.into());
        }

        println!("コンテストの設定が完了しました");
        Ok(())
    }
} 