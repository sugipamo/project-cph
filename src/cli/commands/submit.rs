use crate::cli::Site;
use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::contest::Contest;
use crate::oj::{OJContainer, ProblemInfo};
use crate::config::Config;
use std::path::PathBuf;

pub struct SubmitCommand {
    pub site: Site,
    pub workspace_path: PathBuf,
}

impl SubmitCommand {
    pub fn new(site: Site, workspace_path: PathBuf) -> Self {
        Self { site, workspace_path }
    }

    fn get_problem_url(&self, contest_id: &str, problem_id: &str) -> Result<String> {
        // config/mod.rsを使用して設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // サイトのURLパターンを設定から取得
        let url_pattern = config.get::<String>(&format!("sites.{}.problem_url", self.site.to_string().to_lowercase()))
            .unwrap_or_else(|_| match self.site {
                Site::AtCoder => "https://atcoder.jp/contests/{}/tasks/{}_{}"
                    .to_string(),
            });

        Ok(url_pattern.replace("{contest_id}", contest_id)
            .replace("{problem_id}", problem_id))
    }
}

#[async_trait::async_trait]
impl Command for SubmitCommand {
    async fn execute(&self, command: &Commands) -> Result<()> {
        let problem_id = match command {
            Commands::Submit { problem_id } => problem_id,
            _ => return Err("不正なコマンドです".into()),
        };

        // config/mod.rsを使用して設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // コンテストを読み込む
        println!("コンテストの設定を読み込んでいます...");
        let contest = Contest::new(self.workspace_path.clone())?;

        // 言語IDを取得
        let language_id = match &contest.language {
            Some(lang) => {
                // エイリアス解決を使用して言語名を取得
                let resolved = config.get_with_alias::<String>(&format!("{}.name", lang))
                    .map_err(|_| format!("無効な言語です: {}", lang))?;

                // サイトIDを取得
                config.get::<String>(&format!("{}.site_ids._fallback.{}", resolved, self.site.to_string().to_lowercase()))
                    .map_err(|_| format!("言語IDが設定されていません: {}", resolved))?
            },
            None => {
                println!("言語が設定されていません");
                return Err("言語が設定されていません".into());
            }
        };

        // 問題URLを生成
        let url = self.get_problem_url(&contest.contest_id, problem_id)?;

        // ソースファイルのパスを取得
        let source_path = contest.get_solution_path(problem_id)?;
        if !source_path.exists() {
            return Err(format!("ソースファイルが見つかりません: {}", source_path.display()).into());
        }

        // OJコンテナを初期化
        println!("OJコンテナを初期化しています...");
        let oj = OJContainer::new(self.workspace_path.clone())?;

        // 問題情報を取得
        let problem = ProblemInfo {
            url: url.clone(),
            id: problem_id.to_string(),
            language_id: language_id.clone(),
        };

        // 提出を実行
        println!("提出を実行しています...");
        println!("URL: {}", url);
        println!("言語ID: {}", language_id);
        oj.submit(&problem, &source_path).await?;

        println!("提出が完了しました");
        Ok(())
    }
} 