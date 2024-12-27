use clap::Parser;
use std::path::PathBuf;
use crate::{Language, error::{Result, Error}, workspace::Workspace};
use std::process::Command as StdCommand;
use std::process::Output;
use std::fs;

const EDITORS: &[&str] = &["code", "cursor"];

#[derive(Debug, Clone, Copy, clap::ValueEnum, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Site {
    #[clap(name = "atcoder", alias = "at-coder", alias = "at_coder")]
    AtCoder,
    #[clap(name = "codeforces", alias = "cf")]
    Codeforces,
}

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
pub enum Command {
    /// AtCoder commands
    #[command(name = "atcoder")]
    AtCoder {
        #[command(subcommand)]
        command: AtCoderCommand,
    },

    /// Codeforces commands
    #[command(name = "codeforces")]
    Codeforces {
        #[command(subcommand)]
        command: CodeforcesCommand,
    },
}

#[derive(Parser)]
pub enum AtCoderCommand {
    /// Login to AtCoder
    Login,

    /// Set the current workspace
    #[command(alias = "work", alias = "w")]
    Workspace {
        contest_id: String,
    },

    /// Set the programming language
    #[command(alias = "lang", alias = "l")]
    Language {
        #[arg(value_enum)]
        language: Language,
    },

    /// Open a problem in browser and editor
    #[command(alias = "o")]
    Open {
        problem_id: String,
    },

    /// Test a problem
    Test {
        problem_id: String,
    },

    /// Submit a problem
    Submit {
        problem_id: String,
    },
}

#[derive(Parser)]
pub enum CodeforcesCommand {
    /// Login to Codeforces
    Login,

    /// Set the current workspace
    #[command(alias = "work", alias = "w")]
    Workspace {
        contest_id: String,
    },

    /// Set the programming language
    #[command(alias = "lang", alias = "l")]
    Language {
        #[arg(value_enum)]
        language: Language,
    },

    /// Open a problem in browser and editor
    Open {
        problem_id: String,
    },

    /// Test a problem
    Test {
        problem_id: String,
    },

    /// Submit a problem
    Submit {
        problem_id: String,
    },
}

impl Command {
    pub async fn run() -> Result<()> {
        let command = Self::parse();

        match command {
            Command::AtCoder { command } => match command {
                AtCoderCommand::Login => {
                    // テスト時はログインをスキップ
                    if std::env::var("TEST_MODE").is_ok() {
                        return Ok(());
                    }

                    // テスト時は環境変数からユーザー名とパスワードを取得
                    let (username, password) = if let (Ok(u), Ok(p)) = (std::env::var("USERNAME"), std::env::var("PASSWORD")) {
                        (u, p)
                    } else {
                        println!("AtCoder username:");
                        let mut username = String::new();
                        std::io::stdin().read_line(&mut username)?;
                        let username = username.trim().to_string();

                        let password = rpassword::prompt_password("AtCoder password: ")?;
                        (username, password)
                    };
                    
                    // oj-apiを使用してログイン
                    let output = run_command(
                        "oj",
                        &["login", "https://atcoder.jp"],
                        Some(&[("USERNAME", &username), ("PASSWORD", &password)])
                    )?;

                    if !output.status.success() {
                        return Err(Error::command_failed("oj login", String::from_utf8_lossy(&output.stderr).into_owned()));
                    }

                    println!("Successfully logged in to AtCoder!");
                }
                AtCoderCommand::Workspace { contest_id } => {
                    let mut workspace = Workspace::new(std::env::current_dir()?);
                    workspace.set_workspace(&contest_id, Site::AtCoder)?;
                    println!("Workspace set to {}", contest_id);
                }
                AtCoderCommand::Language { language } => {
                    let mut workspace = Workspace::new(std::env::current_dir()?);
                    workspace.set_language(language)?;
                    println!("Language set to {}", language);
                }
                AtCoderCommand::Open { problem_id } => {
                    let mut workspace = Workspace::new(std::env::current_dir()?);
                    let config = workspace.get_current_config()
                        .ok_or_else(|| Error::InvalidInput("No active contest. Use 'workspace' command to set one.".to_string()))?;
                    let contest_id = config.contest.clone();

                    let source_path = workspace.setup_problem(&problem_id)?;

                    // エディタとブラウザで開く
                    open_in_editor(&source_path)?;
                    open_in_browser(&Site::AtCoder.problem_url(&contest_id, &problem_id))?;
                }
                AtCoderCommand::Test { problem_id: _ } => {
                    let workspace = Workspace::new(std::env::current_dir()?);
                    let _config = workspace.get_current_config()
                        .ok_or_else(|| Error::InvalidInput("No active contest. Use 'workspace' command to set one.".to_string()))?;

                    // テストの実行
                    Error::unsupported_feature("test command")?;
                }
                AtCoderCommand::Submit { problem_id: _ } => {
                    let workspace = Workspace::new(std::env::current_dir()?);
                    let _config = workspace.get_current_config()
                        .ok_or_else(|| Error::InvalidInput("No active contest. Use 'workspace' command to set one.".to_string()))?;

                    // 提出の実行
                    Error::unsupported_feature("submit command")?;
                }
            },
            Command::Codeforces { command: _ } => {
                Error::unsupported_feature("Codeforces commands")?;
            }
        }

        Ok(())
    }
}

impl Site {
    const ATCODER_URL: &'static str = "https://atcoder.jp";
    const CODEFORCES_URL: &'static str = "https://codeforces.com";

    pub fn base_url(&self) -> &'static str {
        match self {
            Site::AtCoder => Self::ATCODER_URL,
            Site::Codeforces => Self::CODEFORCES_URL,
        }
    }

    pub fn problem_url(&self, contest_id: &str, problem_id: &str) -> String {
        match self {
            Site::AtCoder => format!("{}/contests/{}/tasks/{}_{}", 
                self.base_url(), contest_id, contest_id, problem_id),
            Site::Codeforces => format!("{}/contest/{}/problem/{}", 
                self.base_url(), contest_id, problem_id.to_uppercase()),
        }
    }
}

fn run_command(program: &str, args: &[&str], envs: Option<&[(&str, &str)]>) -> Result<Output> {
    let mut cmd = StdCommand::new(program);
    cmd.args(args);
    
    if let Some(env_vars) = envs {
        for (key, value) in env_vars {
            cmd.env(key, value);
        }
    }
    
    cmd.output()
        .map_err(|e| Error::command_failed(program, e.to_string()))
}

fn open_in_editor(path: &PathBuf) -> Result<()> {
    let path_str = path.to_str()
        .ok_or_else(|| Error::InvalidInput("Invalid path".to_string()))?;

    // テスト時はエディタを開かない
    if std::env::var("TEST_MODE").is_ok() {
        return Ok(());
    }

    for editor in EDITORS {
        if run_command(editor, &[path_str], None).is_ok() {
            return Ok(());
        }
    }
    Ok(())
}

fn open_in_browser(url: &str) -> Result<()> {
    // テスト時はブラウザを開かない
    if std::env::var("TEST_MODE").is_ok() {
        return Ok(());
    }

    open::that(url).map_err(|e| Error::command_failed("open browser", e.to_string()))
} 