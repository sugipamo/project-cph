use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::contest::Contest;
use crate::config::Config;
use crate::oj::{OJContainer, ProblemInfo};

#[derive(Debug)]
pub struct SubmitCommand {
    problem_id: String,
}

impl SubmitCommand {
    pub fn new(problem_id: String) -> Self {
        Self { problem_id }
    }
}

#[async_trait::async_trait]
impl Command for SubmitCommand {
    async fn execute(&self, _command: &Commands, site_id: &str) -> Result<()> {
        // 設定を取得
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストオブジェクトを作成
        let mut contest = Contest::new(&config, &self.problem_id)?;
        contest.set_site(site_id)?;

        // ソースファイルのパスを取得
        let source_path = contest.get_solution_path(&self.problem_id)?;

        // 言語情報を取得
        let language = contest.get_solution_language()?;

        // 言語IDを取得
        let language_id = contest.get_config::<String>(&format!(
            "languages.{}.site_ids._fallback.{}",
            language,
            site_id.to_lowercase()
        ))?;

        // 問題URLを取得
        let url = contest.get_problem_url(&self.problem_id)?;

        // 問題情報を構築
        let problem = ProblemInfo {
            url,
            source_path: source_path.clone(),
            problem_id: self.problem_id.clone(),
        };

        // ワークスペースディレクトリを取得
        let workspace_path = std::env::current_dir()?;

        // OJコンテナを初期化して提出
        let oj = OJContainer::new(workspace_path, contest)?;
        oj.submit(&problem, &language_id).await?;

        Ok(())
    }
} 