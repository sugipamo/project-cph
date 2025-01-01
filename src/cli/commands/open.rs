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
            Site::AtCoder => format!("https://atcoder.jp/contests/{}/tasks/{}_{}", contest_id, contest_id, problem_id),
        }
    }
}

#[async_trait::async_trait]
impl Command for OpenCommand {
    async fn execute(&self, command: &Commands) -> Result<()> {
        let contest = Contest::new(self.workspace_path.clone())?;
        let problem_id = match command {
            Commands::Open { problem_id } => problem_id,
            _ => return Err("不正なコマンドです".into()),
        };

        // 言語設定を確認
        println!("言語設定を読み込んでいます...");
        let config_paths = config::get_config_paths();
        let lang_config = LanguageConfig::load(config_paths.languages)?;

        // 言語が設定されているか確認
        if let Some(lang) = &contest.language {
            if lang_config.resolve_language(lang).is_none() {
                return Err(format!("未知の言語です: {}", lang).into());
            }
        }

        // 問題URLを生成
        let url = self.get_problem_url(&contest.contest_id, problem_id);

        // OJコンテナを初期化
        let oj = OJContainer::new(self.workspace_path.clone())?;

        // 問題ディレクトリの作成
        contest.create_problem_directory(problem_id)?;

        let problem = ProblemInfo {
            url: url.clone(),
            source_path: contest.get_solution_path(problem_id)?,
            problem_id: problem_id.clone(),
        };

        // エディタで開く
        if let Err(e) = open_in_cursor(&url, Some(&problem.source_path)) {
            println!("Note: エディタでの表示に失敗しました: {}", e);
            // エディタでの表示失敗は重大なエラーではない
        }

        // 非同期で問題を開く
        if let Err(e) = oj.open(problem.clone()).await {
            println!("問題を開く際にエラーが発生しました: {}", e);
            // 重大なエラーではないため、処理を継続
        }
        
        Ok(())
    }
} 