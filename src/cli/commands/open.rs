use crate::error::Result;
use crate::cli::{Site, Commands};
use crate::cli::commands::Command;
use crate::contest::Contest;
use crate::config::Config;
use open;

pub struct OpenCommand {
    site: Site,
    problem_id: String,
}

impl OpenCommand {
    pub fn new(site: Site, problem_id: String) -> Self {
        Self { site, problem_id }
    }
}

#[async_trait::async_trait]
impl Command for OpenCommand {
    async fn execute(&self, _command: &Commands) -> Result<()> {
        // 設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストディレクトリを取得
        let contest = Contest::new(&config, &self.problem_id)?;

        // ソースファイルのパスを取得
        let source_path = contest.get_solution_path(&self.problem_id)?;

        // 問題URLを取得
        let url = self.site.get_problem_url(&self.problem_id);

        // ブラウザで問題ページを開く
        if let Some(url) = url {
            open::that(url)?;
        }

        // エディタでソースファイルを開く
        if let Some(editor) = config.get::<String>("system.editors.0").ok() {
            std::process::Command::new(editor)
                .arg(&source_path)
                .spawn()?;
        }

        Ok(())
    }
} 