use super::{Command, Result, CommandContext};
use crate::cli::Commands;
use crate::contest::Contest;
use std::path::PathBuf;
use std::fs;

pub struct GenerateCommand {
    context: CommandContext,
}

impl GenerateCommand {
    pub fn new(context: CommandContext) -> Self {
        Self { context }
    }

    /// 生成スクリプトを探す
    fn find_generator(&self, problem_id: &str) -> Option<PathBuf> {
        let generator_path = self.context.active_contest_dir
            .join("template")
            .join(format!("{}_gen.rs", problem_id));

        if generator_path.exists() {
            Some(generator_path)
        } else {
            None
        }
    }

    /// テンプレートファイルを探す
    fn find_template(&self, language: &str) -> Option<PathBuf> {
        let extension = match language {
            "python" => "py",
            "cpp" => "cpp",
            "rust" => "rs",
            _ => language,
        };

        let template_path = self.context.active_contest_dir
            .join("template")
            .join(format!("main.{}", extension));

        if template_path.exists() {
            Some(template_path)
        } else {
            None
        }
    }

    /// テンプレートからファイルを生成
    fn generate_from_template(&self, template_path: &PathBuf, target_path: &PathBuf) -> Result<()> {
        if let Err(e) = fs::copy(template_path, target_path) {
            println!("テンプレートのコピーに失敗しました: {}", e);
            return Err(e.into());
        }
        println!("ソースファイルを生成しました: {}", target_path.display());
        Ok(())
    }

    /// 生成スクリプトを実行
    fn run_generator(&self, generator_path: &PathBuf) -> Result<()> {
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

        // コンテストを読み込む
        let contest = match Contest::new(self.context.active_contest_dir.clone()) {
            Ok(contest) => contest,
            Err(e) => {
                println!("コンテストの読み込みに失敗しました: {}", e);
                return Err(e.into());
            }
        };

        // 生成スクリプトを探す
        if let Some(generator_path) = self.find_generator(problem_id) {
            // 2回目の実行: 生成スクリプトを実行
            return self.run_generator(&generator_path);
        }

        // ワンプレートを探す
        let template_path = self.find_template(&contest.language.to_string())
            .ok_or_else(|| {
                let err = format!("テンプレートが見つかりません: template/main.{}", contest.language.to_string());
                println!("{}", err);
                err
            })?;

        // ソースファイルのパスを取得
        let source_path = contest.get_source_path(problem_id);

        // テンプレートからファイルを生成
        self.generate_from_template(&template_path, &source_path)?;

        // 生成スクリプトのテンプレートをコピー
        let template_generator = self.context.active_contest_dir
            .join("template")
            .join("gen.rs");
        let target_generator = self.context.active_contest_dir
            .join("template")
            .join(format!("{}_gen.rs", problem_id));

        if template_generator.exists() && !target_generator.exists() {
            if let Err(e) = fs::copy(&template_generator, &target_generator) {
                println!("生成スクリプトのテンプレートのコピーに失敗しました: {}", e);
                return Err(e.into());
            }
            println!("\n生成スクリプトのテンプレートを作成しました: {}", target_generator.display());
            println!("次回の実行時に生成スクリプトが使用されます。");
        }

        Ok(())
    }
} 