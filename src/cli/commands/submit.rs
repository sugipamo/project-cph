use crate::error::Result;
use crate::cli::Commands;
use crate::cli::commands::Command;
use crate::contest::Contest;
use crate::oj::{OJContainer, ProblemInfo};
use crate::config::Config;

pub struct SubmitCommand {
    site_id: String,
    problem_id: String,
}

impl SubmitCommand {
    pub fn new(site_id: String, problem_id: String) -> Self {
        Self { site_id, problem_id }
    }
}

#[async_trait::async_trait]
impl Command for SubmitCommand {
    async fn execute(&self, _command: &Commands) -> Result<()> {
        // 設定を取得
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストディレクトリを取得
        let mut contest = Contest::new(&config, &self.problem_id)?;

        // サイトを設定
        contest.set_site(&self.site_id)?;

        // ソースファイルのパスを取得
        let source_path = contest.get_solution_path(&self.problem_id)?;

        // 言語情報を取得
        let language = contest.get_solution_language()?;

        // 言語IDを取得
        let language_id = config
            .get::<String>(&format!(
                "languages.{}.site_ids._fallback.{}",
                language,
                self.site_id.to_lowercase()
            ))
            .map_err(|_| format!("言語 {} の設定が見つかりません", language))?;

        // 問題URLを取得
        let url = contest.get_problem_url()
            .map_err(|_| format!("問題URLの生成に失敗しました: {}", self.problem_id))?;

        // 問題情報を構築
        let problem = ProblemInfo {
            url,
            source_path: source_path.clone(),
            problem_id: self.problem_id.clone(),
        };

        // 提出を実行
        let workspace_path = std::env::current_dir()?;
        let oj = OJContainer::new(workspace_path, contest)?;
        oj.submit(&problem, &language_id).await?;

        Ok(())
    }
} 