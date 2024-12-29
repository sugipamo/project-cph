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

    /// テンプレートからソースファイルを生成
    fn generate_from_template(&self, template_path: &PathBuf, target_path: &PathBuf) -> Result<()> {
        if target_path.exists() {
            return Err(format!("ファイルが既に存在します: {}", target_path.display()).into());
        }

        fs::copy(template_path, target_path)?;
        println!("ソースファイルを生成しました: {}", target_path.display());
        Ok(())
    }

    /// 生成スクリプトを実行
    fn run_generator(&self, generator_path: &PathBuf) -> Result<()> {
        println!("生成スクリプトを実行します: {}", generator_path.display());
        println!("この機能は開発中です。以下のコマンドで実行してください:");
        println!("cph {}", generator_path.display());
        Ok(())
    }
}

impl Command for GenerateCommand {
    fn execute(&self, command: &Commands) -> Result<()> {
        let contest = Contest::new(self.context.active_contest_dir.clone())?;
        let problem_id = match command {
            Commands::Generate { problem_id } => problem_id,
            _ => return Err("不正なコマンドです".into()),
        };

        // 生成スクリプトを探す
        if let Some(generator_path) = self.find_generator(problem_id) {
            // 2回目の実行: 生成スクリプトを実行
            return self.run_generator(&generator_path);
        }

        // ワンプレートを探す
        let template_path = self.find_template(&contest.language.to_string())
            .ok_or_else(|| format!("テンプレートが見つかりません: template/main.{}", contest.language.to_string()))?;

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
            fs::copy(&template_generator, &target_generator)?;
            println!("\n生成スクリプトのテンプレートを作成しました: {}", target_generator.display());
            println!("次回の実行時に生成スクリプトが使用されます。");
        }

        Ok(())
    }
} 