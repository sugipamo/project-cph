use std::path::PathBuf;
use clap::ArgMatches;
use serde::Deserialize;
use crate::oj::{OJContainer, ProblemInfo};
use super::{Command, CommandContext, Result};

#[derive(Debug, Deserialize)]
struct ContestConfig {
    contest_id: String,
    language: Option<String>,
}

/// 提出コマンド
pub struct SubmitCommand {
    context: CommandContext,
}

impl SubmitCommand {
    pub fn new(context: CommandContext) -> Self {
        Self { context }
    }

    /// 設定ファイルを読み込む
    fn load_config(&self, config_path: &PathBuf) -> Result<ContestConfig> {
        if config_path.exists() {
            let content = std::fs::read_to_string(config_path)?;
            Ok(serde_yaml::from_str(&content)
                .map_err(|e| format!("設定ファイルの解析に失敗しました: {}", e))?)
        } else {
            Err("contests.yamlが見つかりません".into())
        }
    }

    /// 現在のディレクトリからcontests.yamlを探す
    fn find_config_file(&self) -> Option<PathBuf> {
        let mut current_dir = self.context.workspace_path.clone();
        while current_dir.parent().is_some() {
            let config_path = current_dir.join("contests.yaml");
            if config_path.exists() {
                return Some(config_path);
            }
            current_dir = current_dir.parent().unwrap().to_path_buf();
        }
        None
    }

    /// コンテスト情報を取得
    fn get_contest_info(&self) -> Result<ContestConfig> {
        let config_path = self.find_config_file()
            .ok_or("contests.yamlが見つかりません。workコマンドでワークスペースを作成してください。")?;
        
        self.load_config(&config_path)
    }

    /// ソースファイルのパスを取得
    fn get_source_path(&self, contest_id: &str, problem_id: &str, language: &str) -> PathBuf {
        let extension = match language {
            "python" => "py",
            "cpp" => "cpp",
            "rust" => "rs",
            _ => language,
        };
        
        self.context.workspace_path
            .join(contest_id)
            .join(format!("{}.{}", problem_id, extension))
    }
}

impl Command for SubmitCommand {
    fn execute(&self, matches: &ArgMatches) -> Result<()> {
        let problem_id = matches.get_one::<String>("problem_id")
            .ok_or("問題IDが指定されていません")?;

        // コンテスト情報を取得
        let config = self.get_contest_info()?;
        let language = config.language
            .ok_or("言語が設定されていません。languageコマンドで設定してください。")?;

        let url = format!(
            "https://atcoder.jp/contests/{}/tasks/{}_{}", 
            config.contest_id,
            config.contest_id,
            problem_id
        );

        // ソースファイルのパスを取得
        let source_path = self.get_source_path(&config.contest_id, problem_id, &language);
        if !source_path.exists() {
            return Err(format!("ソースファイルが見つかりません: {}", source_path.display()).into());
        }

        // OJContainerを初期化
        let oj = OJContainer::new(self.context.workspace_path.clone())?;

        // 問題情報を作成
        let problem_info = ProblemInfo {
            url: url.clone(),
            source_path,
            problem_id: problem_id.to_string(),
        };

        // 提出を実行
        tokio::runtime::Runtime::new()?.block_on(async {
            oj.submit(&problem_info, &self.context.site, &language).await
        })?;

        Ok(())
    }
} 