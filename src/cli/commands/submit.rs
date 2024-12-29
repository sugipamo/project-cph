use crate::cli::Site;
use crate::cli::commands::{Command, Result};
use crate::config::Config;
use crate::oj::{OJContainer, ProblemInfo};
use clap::ArgMatches;
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
    fn execute(&self, matches: &ArgMatches) -> Result<()> {
        let problem_id = matches.get_one::<String>("problem_id")
            .ok_or("問題IDが指定されていません")?;

        // 設定を読み込む
        let config = Config::load(&self.workspace_path)?;

        // ソースファイルのパスを構築
        let source_path = self.workspace_path
            .join("src")
            .join(format!("{}.{}", problem_id, config.language.extension()));

        if !source_path.exists() {
            return Err(format!("ソースファイルが見つかりません: {}", source_path.display()).into());
        }

        // OJコンテナを初期化
        let oj = OJContainer::new(self.workspace_path.clone())?;

        // 提出を実行
        tokio::runtime::Runtime::new()?.block_on(async {
            let problem = ProblemInfo {
                url: self.get_problem_url(&config.contest_id, problem_id),
                source_path: source_path.clone(),
                problem_id: problem_id.clone(),
            };

            let language_id = config.language.get_id(&self.site);
            oj.submit(&problem, &self.site, language_id).await?;
            println!("提出が完了しました");
            Ok(())
        })
    }
} 