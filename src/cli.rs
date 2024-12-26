use std::process::Command;
use clap::{Parser, Subcommand};
use crate::error::Result;
use crate::Language;
use crate::workspace::Workspace;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
pub struct Cli {
    /// コンテストID（例：abc123）
    contest_id: String,

    /// プログラミング言語
    #[arg(value_enum)]
    language: Language,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// 問題を開く
    Open {
        /// 問題ID（例：a, b, c）
        problem_id: String,
    },
}

impl Cli {
    pub async fn run() -> Result<()> {
        let cli = Self::parse();
        match cli.command {
            Commands::Open { problem_id } => {
                open_problem(&cli.contest_id, &problem_id, cli.language).await
            }
        }
    }
}

async fn open_problem(contest_id: &str, problem_id: &str, language: Language) -> Result<()> {
    // コンテストIDのバリデーション
    if !is_valid_contest_id(contest_id) {
        return Err(crate::error::Error::InvalidInput(format!("Invalid contest ID: {}", contest_id)));
    }

    // 問題IDのバリデーション
    if !is_valid_problem_id(problem_id) {
        return Err(crate::error::Error::InvalidInput(format!("Invalid problem ID: {}", problem_id)));
    }

    // ワークスペースのセットアップ
    let workspace = Workspace::new()?;
    let source_file = workspace.setup_problem(contest_id, problem_id, language)?;

    // エディタでファイルを開く
    if !open_in_editor(&source_file.to_string_lossy())? {
        println!("Warning: Failed to open editor. File location: {}", source_file.display());
    }

    // ブラウザで問題ページを開く
    let url = workspace.get_problem_url(contest_id, problem_id);
    if let Err(e) = open::that(&url) {
        println!("Warning: Failed to open browser: {}. URL: {}", e, url);
    }

    Ok(())
}

fn is_valid_contest_id(contest_id: &str) -> bool {
    // abc123形式のバリデーション
    contest_id.len() >= 4 
        && contest_id[..3].chars().all(|c| c.is_ascii_lowercase())
        && contest_id[3..].chars().all(|c| c.is_ascii_digit())
}

fn is_valid_problem_id(problem_id: &str) -> bool {
    // a-h形式のバリデーション
    problem_id.len() == 1 && problem_id.chars().next().unwrap().is_ascii_lowercase()
}

fn open_in_editor(file_path: &str) -> Result<bool> {
    // VSCode を試す
    if Command::new("code")
        .arg(file_path)
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
    {
        return Ok(true);
    }

    // Cursor を試す
    if Command::new("cursor")
        .arg(file_path)
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
    {
        return Ok(true);
    }

    Ok(false)
} 