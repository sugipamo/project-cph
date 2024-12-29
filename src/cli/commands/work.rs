use std::path::{Path, PathBuf};
use std::fs;
use super::{Command, Result};
use crate::cli::Commands;
use crate::workspace::Workspace;
use crate::config::Config;

pub struct WorkCommand {
    pub workspace_path: PathBuf,
    pub project_root: PathBuf,
}

impl WorkCommand {
    pub fn new(workspace_path: PathBuf) -> Self {
        Self { 
            workspace_path: workspace_path.join("workspace"),
            project_root: workspace_path,
        }
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
        let template_path = self.project_root.join("src").join("templates").join("contests.yaml");
        if template_path.exists() {
            Some(template_path)
        } else {
            None
        }
    }

    /// テンプレートの.moveignoreを探す
    fn find_template_moveignore(&self) -> Option<PathBuf> {
        let template_path = self.project_root.join("src").join("templates").join(".moveignore");
        if template_path.exists() {
            Some(template_path)
        } else {
            None
        }
    }

    /// ワークスペースのディレクトリ構造を作成
    fn create_workspace_structure(&self, contest_id: &str) -> Result<()> {
        // workspaceディレクトリが存在しない場合は作成
        if !self.workspace_path.exists() {
            fs::create_dir_all(&self.workspace_path)?;
        }

        // 基本ディレクトリを作成
        fs::create_dir_all(&self.workspace_path)?;
        fs::create_dir_all(self.workspace_path.join("src"))?;
        fs::create_dir_all(self.workspace_path.join("test"))?;
        fs::create_dir_all(self.workspace_path.join("template"))?;

        // 初期設定を作成
        let config = Config {
            contest_id: contest_id.to_string(),
            language: crate::Language::Rust,
            site: crate::cli::Site::AtCoder,
        };

        // 設定を保存
        let config_str = serde_yaml::to_string(&config)?;
        std::fs::write(self.workspace_path.join("contests.yaml"), config_str)?;

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
        self.create_workspace_structure(contest_id)?;

        // ワークスペースを初期化
        let workspace = Workspace::new(self.workspace_path.clone())?;

        println!("ワークスペースを作成しました: {}", self.workspace_path.display());
        Ok(())
    }
} 