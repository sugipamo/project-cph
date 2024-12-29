use std::path::PathBuf;
use clap::ArgMatches;
use serde::Deserialize;
use crate::oj::{OJContainer, ProblemInfo};
use super::{Command, CommandContext, Result};

#[derive(Debug, Deserialize)]
struct ContestConfig {
    contest_id: String,
}

/// 問題を開くコマンド
pub struct OpenCommand {
    context: CommandContext,
}

impl OpenCommand {
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

    /// コンテストIDを取得
    fn get_contest_id(&self) -> Result<String> {
        let config_path = self.find_config_file()
            .ok_or("contests.yamlが見つかりません。workコマンドでワークスペースを作成してください。")?;
        
        let config = self.load_config(&config_path)?;
        Ok(config.contest_id)
    }
}

impl Command for OpenCommand {
    fn execute(&self, matches: &ArgMatches) -> Result<()> {
        let problem_id = matches.get_one::<String>("problem_id")
            .ok_or("問題IDが指定されていません")?;

        let contest_id = self.get_contest_id()?;
        let url = format!(
            "https://atcoder.jp/contests/{}/tasks/{}_{}", 
            contest_id, 
            contest_id, 
            problem_id
        );

        // VSCode/Cursorで開くためのURL
        let editor_url = format!("vscode://file{}/workspace/{}/test/{}", 
            self.context.workspace_path.display(),
            contest_id,
            problem_id
        );

        // OJContainerを初期化
        let oj = OJContainer::new(self.context.workspace_path.clone())?;

        // 問題情報を作成
        let problem_info = ProblemInfo {
            url: url.clone(),
            source_path: PathBuf::new(), // 実際のソースパスが必要な場合は設定
            problem_id: problem_id.to_string(),
        };

        // テストケースのダウンロードとブラウザでの表示
        tokio::runtime::Runtime::new()?.block_on(async {
            oj.open(problem_info).await
        })?;

        // エディタで開く
        if let Err(e) = open_in_cursor(&editor_url) {
            println!("Note: エディタでの表示に失敗しました: {}", e);
        }

        Ok(())
    }
} 