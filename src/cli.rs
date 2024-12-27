use clap::Parser;
use std::path::PathBuf;
use crate::{Language, error::{Result, Error}, workspace::Workspace};
use std::process::Command as StdCommand;
use std::process::Output;

#[derive(Debug, Clone, Copy, clap::ValueEnum, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Site {
    #[clap(name = "atcoder", alias = "at-coder", alias = "at_coder")]
    AtCoder,
    #[clap(name = "codeforces", alias = "cf")]
    Codeforces,
}

impl std::fmt::Display for Site {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Site::AtCoder => write!(f, "AtCoder"),
            Site::Codeforces => write!(f, "Codeforces"),
        }
    }
}

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
pub struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Parser)]
pub enum Command {
    /// AtCoder commands
    #[command(name = "atcoder", alias = "at-coder", alias = "at_coder")]
    AtCoder {
        #[command(subcommand)]
        command: CommonSubCommand,
    },

    /// Codeforces commands
    #[command(name = "codeforces", alias = "cf")]
    Codeforces {
        #[command(subcommand)]
        command: CommonSubCommand,
    },
}

#[derive(Parser)]
pub enum CommonSubCommand {
    /// Login to the platform
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

impl Cli {
    pub async fn run() -> Result<()> {
        let cli = Self::parse();

        match cli.command {
            Command::AtCoder { command } => handle_command(command, Site::AtCoder),
            Command::Codeforces { command } => handle_command(command, Site::Codeforces),
        }
    }
}

fn handle_command(command: CommonSubCommand, site: Site) -> Result<()> {
    match command {
        CommonSubCommand::Login => handle_login(site),
        CommonSubCommand::Workspace { contest_id } => handle_workspace(contest_id, site),
        CommonSubCommand::Language { language } => handle_language(language),
        CommonSubCommand::Open { problem_id } => handle_open(problem_id, site),
        CommonSubCommand::Test { problem_id } => handle_test(problem_id),
        CommonSubCommand::Submit { problem_id } => handle_submit(problem_id),
    }
}

fn handle_login(site: Site) -> Result<()> {
    // テスト時はログインをスキップ
    if std::env::var("TEST_MODE").is_ok() {
        return Ok(());
    }

    // テスト時は環境変数からユーザー名とパスワードを取得
    let (username, password) = if let (Ok(u), Ok(p)) = (std::env::var("USERNAME"), std::env::var("PASSWORD")) {
        (u, p)
    } else {
        println!("{} username:", site);
        let mut username = String::new();
        std::io::stdin().read_line(&mut username)?;
        let username = username.trim().to_string();

        let password = rpassword::prompt_password(&format!("{} password: ", site))?;
        (username, password)
    };
    
    // oj-apiを使用してログイン
    let output = run_command(
        "oj",
        &["login", site.base_url()],
        Some(&[("USERNAME", &username), ("PASSWORD", &password)])
    )?;

    if !output.status.success() {
        return Err(Error::command_failed("oj login", String::from_utf8_lossy(&output.stderr).into_owned()));
    }

    println!("Successfully logged in to {}!", site);
    Ok(())
}

fn get_workspace() -> Result<Workspace> {
    Ok(Workspace::new(std::env::current_dir()?))
}

fn get_workspace_with_config() -> Result<(Workspace, crate::workspace::Config)> {
    let workspace = get_workspace()?;
    let config = workspace.get_current_config()
        .ok_or_else(|| Error::InvalidInput(crate::error::NO_ACTIVE_CONTEST.to_string()))?
        .clone();
    Ok((workspace, config))
}

fn handle_workspace(contest_id: String, site: Site) -> Result<()> {
    let mut workspace = get_workspace()?;
    workspace.set_workspace(&contest_id, site)?;
    println!("Workspace set to {}", contest_id);
    Ok(())
}

fn handle_language(language: Language) -> Result<()> {
    let mut workspace = get_workspace()?;
    workspace.set_language(language)?;
    println!("Language set to {}", language);
    Ok(())
}

fn handle_open(problem_id: String, site: Site) -> Result<()> {
    let (mut workspace, config) = get_workspace_with_config()?;
    let contest_id = config.contest.clone();

    let source_path = workspace.setup_problem(&problem_id)?;

    // エディタとブラウザで開く
    open_in_editor(&source_path)?;
    open_in_browser(&site.problem_url(&contest_id, &problem_id))?;
    Ok(())
}

fn handle_test(_problem_id: String) -> Result<()> {
    let (_workspace, _config) = get_workspace_with_config()?;
    Error::unsupported_feature("test command")
}

fn handle_submit(_problem_id: String) -> Result<()> {
    let (_workspace, _config) = get_workspace_with_config()?;
    Error::unsupported_feature("submit command")
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

    for editor in &["code", "cursor"] {
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