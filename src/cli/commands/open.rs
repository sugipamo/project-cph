use crate::cli::Site;
use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::contest::Contest;
use crate::oj::{open_in_cursor, OJContainer, ProblemInfo};
use std::path::PathBuf;

pub struct OpenCommand {
    pub site: Site,
    pub workspace_path: PathBuf,
}

impl OpenCommand {
    pub fn new(site: Site, workspace_path: PathBuf) -> Self {
        Self { site, workspace_path }
    }

    fn get_problem_url(&self, contest_id: &str, problem_id: &str) -> String {
        match self.site {
            Site::AtCoder => format!("https://atcoder.jp/contests/{}/tasks/{}_{}", contest_id, problem_id, problem_id),
        }
    }
}

impl Command for OpenCommand {
    fn execute(&self, command: &Commands) -> Result<()> {
        let contest = Contest::new(self.workspace_path.clone())?;
        let problem_id = match command {
            Commands::Open { problem_id } => problem_id,
            _ => return Err("不正なコマンドです".into()),
        };

        // 問題URLを生成
        let url = self.get_problem_url(&contest.contest_id, problem_id);

        // OJコンテナを初期化
        let oj = OJContainer::new(self.workspace_path.clone())?;

        // 問題を開く
        tokio::runtime::Runtime::new()?.block_on(async {
            let problem = ProblemInfo {
                url: url.clone(),
                source_path: contest.get_source_path(problem_id),
                problem_id: problem_id.clone(),
            };

            oj.open(problem).await?;
            
            // エディタで開く
            if let Err(e) = open_in_cursor(&url) {
                println!("Note: エディタでの表示に失敗しました: {}", e);
            }

            Ok(())
        })
    }
} 