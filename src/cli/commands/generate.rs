use std::path::PathBuf;
use std::fs;
use clap::ArgMatches;
use super::{Command, CommandContext, Result};
use crate::cli::commands::language::ContestConfig;

/// テンプレート生成コマンド
pub struct GenerateCommand {
    context: CommandContext,
}

impl GenerateCommand {
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

    /// 生成スクリプトを探す
    fn find_generator(&self, problem_id: &str) -> Option<PathBuf> {
        let generator_path = self.context.workspace_path
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

        let template_path = self.context.workspace_path
            .join("template")
            .join(format!("main.{}", extension));

        if template_path.exists() {
            Some(template_path)
        } else {
            None
        }
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
    fn execute(&self, matches: &ArgMatches) -> Result<()> {
        let problem_id = matches.get_one::<String>("problem_id")
            .ok_or("問題IDが指定されていません")?;

        // 生成スクリプトを探す
        if let Some(generator_path) = self.find_generator(problem_id) {
            // 2回目の実行: 生成スクリプトを実行
            return self.run_generator(&generator_path);
        }

        // 設定を読み込む
        let config_path = self.find_config_file()
            .ok_or("contests.yamlが見つかりません。workコマンドでワークスペースを作成してください。")?;
        let config = self.load_config(&config_path)?;

        // 言語設定を確認
        let language = config.language
            .ok_or("言語が設定されていません。languageコマンドで設定してください。")?;

        // テンプレートを探す
        let template_path = self.find_template(&language)
            .ok_or(format!("テンプレートが見つかりません: template/main.{}", language))?;

        // ソースファイルのパスを取得
        let source_path = self.get_source_path(&config.contest_id, problem_id, &language);

        // テンプレートからファイルを生成
        self.generate_from_template(&template_path, &source_path)?;

        // 生成スクリプトのテンプレートをコピー
        let template_generator = self.context.workspace_path
            .join("template")
            .join("gen.rs");
        let target_generator = self.context.workspace_path
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