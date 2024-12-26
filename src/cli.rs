use clap::Parser;
use std::path::PathBuf;
use crate::{Language, error::Result, workspace::Workspace};

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
pub struct Cli {
    /// Contest ID (e.g., abc300)
    contest_id: String,

    /// Programming language (rust/r or pypy/py)
    #[arg(value_enum)]
    language: Language,

    /// Command to execute (open/o, test/t, submit/s, or generate/g)
    command: String,

    /// Problem ID (e.g., a, b, c)
    problem_id: String,
}

impl Cli {
    pub async fn run() -> Result<()> {
        let cli = Self::parse();

        // ワークスペースの初期化
        let workspace = Workspace::new(std::env::current_dir()?);

        match cli.command.as_str() {
            "open" | "o" => {
                // 問題を開く
                let source_path = workspace.setup_problem(&cli.contest_id, &cli.problem_id, cli.language)?;

                // エディタとブラウザで開く
                open_in_editor(&source_path)?;
                open_in_browser(&cli.contest_id, &cli.problem_id)?;
            }
            _ => {
                return Err(crate::error::Error::InvalidInput(format!(
                    "invalid command: {}",
                    cli.command
                )));
            }
        }

        Ok(())
    }
}

fn open_in_editor(path: &PathBuf) -> Result<()> {
    if let Err(_) = std::process::Command::new("code")
        .arg(path)
        .status() {
        std::process::Command::new("cursor")
            .arg(path)
            .status()?;
    }
    Ok(())
}

fn open_in_browser(contest_id: &str, problem_id: &str) -> Result<()> {
    let url = format!(
        "https://atcoder.jp/contests/{}/tasks/{}_{}", 
        contest_id, 
        contest_id, 
        problem_id
    );
    open::that(url)?;
    Ok(())
} 