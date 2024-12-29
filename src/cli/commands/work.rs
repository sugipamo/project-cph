use std::path::{PathBuf};
use crate::cli::Site;
use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::workspace::Workspace;

pub struct WorkCommand {
    pub site: Site,
    pub workspace_path: PathBuf,
}

impl WorkCommand {
    pub fn new(site: Site, workspace_path: PathBuf) -> Self {
        Self { site, workspace_path }
    }
}

impl Command for WorkCommand {
    fn execute(&self, command: &Commands) -> Result<()> {
        let contest_id = match command {
            Commands::Work { contest_id } => contest_id,
            _ => return Err("不正なコマンドです".into()),
        };

        // ワークスペースを読み込む
        let mut workspace = Workspace::new(self.workspace_path.clone())?;
        
        // コンテストIDを設定
        workspace.set_contest(contest_id.clone());
        workspace.set_site(self.site.clone());
        
        // 設定を保存
        workspace.save()?;

        println!("コンテストの設定を保存しました: {}", contest_id);
        Ok(())
    }
} 