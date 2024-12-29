use std::path::{PathBuf};
use crate::cli::Site;
use crate::cli::commands::{Command, Result};
use crate::cli::Commands;
use crate::contest::Contest;
use std::fs;

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

        // active_contestディレクトリを作成
        let active_dir = self.workspace_path.join("active_contest");
        if !active_dir.exists() {
            println!("active_contestディレクトリを作成します");
            fs::create_dir_all(&active_dir)?;
        }

        // コンテストを読み込む
        let mut contest = Contest::new(self.workspace_path.clone())?;
        
        // コンテストIDを設定
        contest.set_contest(contest_id.clone());
        contest.set_site(self.site.clone());
        
        // 設定を保存（テンプレートのコピーと既存ファイルの移動も行われる）
        contest.save()?;

        println!("コンテストの設定を保存しました: {}", contest_id);
        println!("テンプレートファイルは {} にコピーされました", active_dir.display());
        Ok(())
    }
} 