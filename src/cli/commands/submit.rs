use crate::cli::Site;
use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::workspace::Workspace;
use crate::oj::{OJContainer, ProblemInfo};
use std::path::PathBuf;

pub struct SubmitCommand {
    pub site: Site,
    pub workspace_path: PathBuf,
}

impl SubmitCommand {
    pub fn new(site: Site, workspace_path: PathBuf) -> Self {
        Self { site, workspace_path }
    }

    fn get_problem_url(&self, contest_id: &str, problem_id: &str) -> String {
        match self.site {
            Site::AtCoder => format!("https://atcoder.jp/contests/{}/tasks/{}_{}", contest_id, contest_id, problem_id),
        }
    }
}

impl Command for SubmitCommand {
    fn execute(&self, command: &Commands) -> Result<()> {
        let problem_id = match command {
            Commands::Submit { problem_id } => problem_id,
            _ => return Err("不正なコマンドです".into()),
        };

        // ワークスペースを読み込む
        let workspace = Workspace::new(self.workspace_path.clone())?;

        // 問題URLを生成
        let url = self.get_problem_url(&workspace.contest_id, problem_id);

        // ソースファイルのパスを取得
        let source_path = workspace.get_source_path(problem_id);
        if !source_path.exists() {
            return Err(format!("ソースファイルが見つかりません: {}", source_path.display()).into());
        }

        // OJコンテナを初期化
        let oj = OJContainer::new(self.workspace_path.clone())?;

        // 提出を実行
        tokio::runtime::Runtime::new()?.block_on(async {
            let problem = ProblemInfo {
                url: url.clone(),
                source_path,
                problem_id: problem_id.clone(),
            };

            let language_id = workspace.language.get_id(&self.site);
            oj.submit(&problem, &self.site, language_id).await?;
            println!("提出が完了しました");
            Ok(())
        })
    }
} 