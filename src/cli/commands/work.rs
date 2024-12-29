use std::path::{Path, PathBuf};
use std::fs;
use clap::ArgMatches;
use super::{Command, CommandContext, Result};

/// ワークスペース作成コマンド
pub struct WorkCommand {
    context: CommandContext,
}

impl WorkCommand {
    pub fn new(context: CommandContext) -> Self {
        Self { context }
    }

    /// コンテストIDが有効かどうかを確認
    /// 基本的な文字種のチェックのみを行う
    fn validate_contest_id(&self, contest_id: &str) -> bool {
        if contest_id.is_empty() {
            return false;
        }
        // 英数字、ハイフン、アンダースコアのみを許可
        contest_id.chars().all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_')
    }

    /// ワークスペースのディレクトリ構造を作成
    fn create_workspace_structure(&self, contest_id: &str) -> Result<()> {
        let workspace_root = &self.context.workspace_path;
        let contest_dir = workspace_root.join(contest_id);
        let test_dir = contest_dir.join("test");

        // コンテストディレクトリを作成
        fs::create_dir_all(&contest_dir)?;
        fs::create_dir_all(&test_dir)?;

        // 問題ディレクトリを作成
        for problem in ['a', 'b', 'c', 'd', 'e', 'f'] {
            fs::create_dir_all(test_dir.join(problem.to_string()))?;
        }

        // contests.yamlをコピー
        if let Some(template_contests_yaml) = self.find_template_contests_yaml() {
            fs::copy(
                template_contests_yaml,
                contest_dir.join("contests.yaml")
            )?;
        }

        // .moveignoreをコピー
        if let Some(template_moveignore) = self.find_template_moveignore() {
            fs::copy(
                template_moveignore,
                contest_dir.join(".moveignore")
            )?;
        }

        Ok(())
    }

    /// テンプレートのcontests.yamlを探す
    fn find_template_contests_yaml(&self) -> Option<PathBuf> {
        let workspace_root = &self.context.workspace_path;
        let template_path = workspace_root.join("template").join("contests.yaml");
        if template_path.exists() {
            Some(template_path)
        } else {
            None
        }
    }

    /// テンプレートの.moveignoreを探す
    fn find_template_moveignore(&self) -> Option<PathBuf> {
        let workspace_root = &self.context.workspace_path;
        let template_path = workspace_root.join("template").join(".moveignore");
        if template_path.exists() {
            Some(template_path)
        } else {
            None
        }
    }
}

impl Command for WorkCommand {
    fn execute(&self, matches: &ArgMatches) -> Result<()> {
        let contest_id = matches.get_one::<String>("contest")
            .ok_or("コンテストIDが指定されていません")?;

        // コンテストIDのバリデーション
        if !self.validate_contest_id(contest_id) {
            return Err(format!("無効なコンテストID: {}（英数字、ハイフン、アンダースコアのみ使用可能）", contest_id).into());
        }

        // ワークスペースの作成
        self.create_workspace_structure(contest_id)?;

        println!("ワークスペースを作成しました: {}", contest_id);
        Ok(())
    }
} 