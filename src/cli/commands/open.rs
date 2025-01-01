use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::contest::Contest;
use crate::config::Config;
use open;

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
    async fn execute(&self, _command: &Commands, site_id: &str) -> Result<()> {
        // 設定を取得
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストオブジェクトを作成
        let mut contest = Contest::new(&config, &self.problem_id)?;
        contest.set_site(site_id)?;

        // 問題ディレクトリを作成し、テンプレートをコピー
        if let Err(e) = contest.create_problem_directory(&self.problem_id) {
            println!("Note: 問題ディレクトリの作成に失敗しました: {}", e);
        }

        // ソースファイルのパスを取得
        let source_path = contest.get_solution_path(&self.problem_id)?;

        // 問題URLを取得
        if let Ok(url) = contest.get_problem_url(&self.problem_id) {
            // ブラウザ設定を確認
            if let Ok(browser) = contest.get_config::<String>("system.browser") {
                if let Err(e) = std::process::Command::new(&browser)
                    .arg(&url)
                    .spawn() {
                    println!("Note: Failed to open URL with configured browser: {}", e);
                    // フォールバック: open::thatを試す
                    if let Err(e) = open::that(&url) {
                        println!("Note: Failed to open URL with default browser: {}", e);
                    }
                }
            } else {
                // 設定がない場合はopen::thatを使用
                if let Err(e) = open::that(&url) {
                    println!("Note: Failed to open URL: {}", e);
                }
            }
        }

        // エディタでソースファイルを開く
        if let Some(editor) = contest.get_config::<String>("system.editors.0").ok() {
            std::process::Command::new(editor)
                .arg(&source_path)
                .spawn()?;
        }

        Ok(())
    }
} 