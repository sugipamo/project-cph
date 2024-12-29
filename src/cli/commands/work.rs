use std::path::{Path, PathBuf};
use std::fs;
use super::{Command, Result};
use crate::cli::Commands;
use crate::workspace::Workspace;

pub struct WorkCommand {
    pub workspace_path: PathBuf,
}

impl WorkCommand {
    pub fn new(workspace_path: PathBuf) -> Self {
        Self { workspace_path }
    }

    /// コンテストIDが有効かどうかを確認
    fn validate_contest_id(&self, contest_id: &str) -> bool {
        if contest_id.is_empty() {
            return false;
        }
        // 英数字、ハイフン、アンダースコアのみを許可
        contest_id.chars().all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_')
    }

    /// テンプレートのcontests.yamlを探す
    fn find_template_contests_yaml(&self) -> Option<PathBuf> {
        let template_path = self.workspace_path.join("template").join("contests.yaml");
        if template_path.exists() {
            Some(template_path)
        } else {
            None
        }
    }

    /// テンプレートの.moveignoreを探す
    fn find_template_moveignore(&self) -> Option<PathBuf> {
        let template_path = self.workspace_path.join("template").join(".moveignore");
        if template_path.exists() {
            Some(template_path)
        } else {
            None
        }
    }

    /// ワークスペースのディレクトリ構造を作成
    fn create_workspace_structure(&self) -> Result<()> {
        // 基本ディレクトリを作成
        fs::create_dir_all(&self.workspace_path)?;
        fs::create_dir_all(self.workspace_path.join("src"))?;
        fs::create_dir_all(self.workspace_path.join("test"))?;

        // テンプレートファイルをコピー
        if let Some(template_contests_yaml) = self.find_template_contests_yaml() {
            fs::copy(
                template_contests_yaml,
                self.workspace_path.join("contests.yaml")
            )?;
        }

        // .moveignoreをコピー
        if let Some(template_moveignore) = self.find_template_moveignore() {
            fs::copy(
                template_moveignore,
                self.workspace_path.join(".moveignore")
            )?;
        }

        // 問題ディレクトリを作成
        let test_dir = self.workspace_path.join("test");
        for problem in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] {
            fs::create_dir_all(test_dir.join(problem.to_string()))?;
        }

        Ok(())
    }
}

impl Command for WorkCommand {
    fn execute(&self, command: &Commands) -> Result<()> {
        let contest_id = match command {
            Commands::Work { contest_id } => contest_id,
            _ => return Err("不正なコマンドです".into()),
        };

        // コンテストIDのバリデーション
        if !self.validate_contest_id(contest_id) {
            return Err(format!("無効なコンテストID: {}（英数字、ハイフン、アンダースコアのみ使用可能）", contest_id).into());
        }

        // ワークスペースの作成
        self.create_workspace_structure()?;

        // ワークスペースを初期化
        let mut workspace = Workspace::new(self.workspace_path.clone())?;
        workspace.set_contest(contest_id.clone());
        workspace.save()?;

        println!("ワークスペースを作成しました: {}", self.workspace_path.display());
        Ok(())
    }
} 