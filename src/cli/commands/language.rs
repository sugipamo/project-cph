use crate::cli::commands::{Command, Result, CommandContext};
use crate::cli::Commands;
use crate::contest::Contest;
use crate::config::Config;

#[derive(Debug)]
pub struct LanguageCommand {
    context: CommandContext,
}

impl LanguageCommand {
    pub fn new(context: CommandContext) -> Self {
        Self { context }
    }
}

#[async_trait::async_trait]
impl Command for LanguageCommand {
    async fn execute(&self, command: &Commands, site_id: &str) -> Result<()> {
        let language = match command {
            Commands::Language { language } => language,
            _ => return Err("不正なコマンドです".into()),
        };

        // 設定を取得
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストオブジェクトを作成
        let mut contest = Contest::new(&config, &self.context.problem_id)?;
        contest.set_site(site_id)?;

        // 言語を設定
        contest.set_language(language)?;

        // 設定を保存
        contest.save()?;

        Ok(())
    }
} 