use clap::Parser;
use std::path::PathBuf;
use crate::{Language, error::Result, workspace::Workspace};

const ATCODER_URL: &str = "https://atcoder.jp";
const CODEFORCES_URL: &str = "https://codeforces.com";

const ATCODER_PROBLEM_PATH: &str = "contests/{contest_id}/tasks/{contest_id}_{problem_id}";
const CODEFORCES_PROBLEM_PATH: &str = "contest/{contest_id}/problem/{problem_id}";

const EDITORS: &[&str] = &["code", "cursor"];

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
pub struct Cli {
    /// Site name (e.g., atcoder, codeforces)
    #[arg(value_enum)]
    site: Site,

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

#[derive(Debug, Clone, Copy, clap::ValueEnum)]
pub enum Site {
    #[clap(name = "atcoder", alias = "at-coder", alias = "at_coder")]
    AtCoder,
    #[clap(name = "codeforces", alias = "cf")]
    Codeforces,
}

impl Site {
    fn get_base_url(&self) -> &'static str {
        match self {
            Site::AtCoder => ATCODER_URL,
            Site::Codeforces => CODEFORCES_URL,
        }
    }

    fn get_path_template(&self) -> &'static str {
        match self {
            Site::AtCoder => ATCODER_PROBLEM_PATH,
            Site::Codeforces => CODEFORCES_PROBLEM_PATH,
        }
    }

    fn format_problem_id(&self, problem_id: &str) -> String {
        match self {
            Site::AtCoder => problem_id.to_string(),
            Site::Codeforces => problem_id.to_uppercase(),
        }
    }

    fn get_problem_url(&self, contest_id: &str, problem_id: &str) -> String {
        let path = self.get_path_template()
            .replace("{contest_id}", contest_id)
            .replace("{problem_id}", &self.format_problem_id(problem_id));
        format!("{}/{}", self.get_base_url(), path)
    }
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
                open_in_browser(&cli.site.get_problem_url(&cli.contest_id, &cli.problem_id))?;
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
    for editor in EDITORS {
        if std::process::Command::new(editor)
            .arg(path)
            .status()
            .is_ok() {
            return Ok(());
        }
    }
    Ok(())
}

fn open_in_browser(url: &str) -> Result<()> {
    open::that(url)?;
    Ok(())
} 