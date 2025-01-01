use super::{Command, Result, CommandContext};
use crate::cli::Commands;
use crate::contest::Contest;
use crate::config::Config;
use std::path::PathBuf;
use std::fs;

pub struct GenerateCommand {
    context: CommandContext,
}

impl GenerateCommand {
    pub fn new(context: CommandContext) -> Self {
        Self { context }
    }

    /// 生成スクリプトのパスを取得
    fn get_generator_path(&self, config: &Config, problem_id: &str) -> Result<PathBuf> {
        let template_dir = config.get::<String>("system.contest_dir.template")
            .unwrap_or_else(|_| "contest_template".to_string());
        
        let workspace_dir = std::env::current_dir()?;
        Ok(workspace_dir.join(&template_dir).join(format!("{}_gen.rs", problem_id)))
    }

    /// 生成スクリプトのテンプレートパスを取得
    fn get_generator_template_path(&self, config: &Config) -> Result<PathBuf> {
        let template_dir = config.get::<String>("system.contest_dir.template")
            .unwrap_or_else(|_| "contest_template".to_string());
        
        let workspace_dir = std::env::current_dir()?;
        Ok(workspace_dir.join(&template_dir).join("gen.rs"))
    }

    /// 生成スクリプトを実行
    async fn run_generator(&self, generator_path: &PathBuf) -> Result<()> {
        // TODO: 生成スクリプトの実装
        println!("Note: 生成スクリプトの実行は未実装です: {}", generator_path.display());
        Ok(())
    }
}

#[async_trait::async_trait]
impl Command for GenerateCommand {
    async fn execute(&self, command: &Commands) -> Result<()> {
        let problem_id = match command {
            Commands::Generate { problem_id } => problem_id,
            _ => return Err("不正なコマンドです".into()),
        };

        // 設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        // 生成スクリプトのパスを取得
        let generator_path = self.get_generator_path(&config, problem_id)?;

        // 生成スクリプトが存在する場合は実行
        if generator_path.exists() {
            println!("生成スクリプトを実行します: {}", generator_path.display());
            return self.run_generator(&generator_path).await;
        }

        // コンテストを読み込む
        let contest = Contest::new(&config, problem_id)?;

        // 問題ディレクトリを作成
        contest.create_problem_directory(problem_id)?;

        // 生成スクリプトのテンプレートをコピー
        let template_path = self.get_generator_template_path(&config)?;
        if template_path.exists() && !generator_path.exists() {
            println!("生成スクリプトのテンプレートをコピーしています...");
            if let Err(e) = fs::copy(&template_path, &generator_path) {
                println!("Warning: 生成スクリプトのテンプレートのコピーに失敗しました: {}", e);
            } else {
                println!("生成スクリプトのテンプレートを作成しました: {}", generator_path.display());
                println!("次回の実行時に生成スクリプトが使用されます");
            }
        }

        println!("問題 {} のテンプレートを生成しました", problem_id);
        Ok(())
    }
} 