use clap::Parser;
use std::path::PathBuf;
use crate::{Language, error::{Result, Error}, workspace::Workspace};
use std::process::Command as StdCommand;
use std::process::Output;

const ATCODER_PROBLEM_PATH: &str = "contests/{contest_id}/tasks/{contest_id}_{problem_id}";
const CODEFORCES_PROBLEM_PATH: &str = "contest/{contest_id}/problem/{problem_id}";

const EDITORS: &[&str] = &["code", "cursor"];

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
pub struct Cli {
    /// Site name (e.g., atcoder, codeforces)
    #[arg(value_enum)]
    site: Site,

    /// Command to execute (login/l, open/o, test/t, submit/s, or generate/g)
    command: String,

    /// Contest ID (e.g., abc300) - Required for all commands except login
    #[arg(required_if_eq("command", "open"))]
    #[arg(required_if_eq("command", "o"))]
    contest_id: Option<String>,

    /// Programming language (rust/r or pypy/py) - Required for all commands except login
    #[arg(value_enum)]
    #[arg(required_if_eq("command", "open"))]
    #[arg(required_if_eq("command", "o"))]
    language: Option<Language>,

    /// Problem ID (e.g., a, b, c) - Required for all commands except login
    #[arg(required_if_eq("command", "open"))]
    #[arg(required_if_eq("command", "o"))]
    problem_id: Option<String>,
}

#[derive(Debug, Clone, Copy, clap::ValueEnum)]
pub enum Site {
    #[clap(name = "atcoder", alias = "at-coder", alias = "at_coder")]
    AtCoder,
    #[clap(name = "codeforces", alias = "cf")]
    Codeforces,
}

impl Site {
    const ATCODER_URL: &'static str = "https://atcoder.jp";
    const CODEFORCES_URL: &'static str = "https://codeforces.com";

    fn get_base_url(&self) -> &'static str {
        match self {
            Site::AtCoder => Self::ATCODER_URL,
            Site::Codeforces => Self::CODEFORCES_URL,
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

impl Cli {
    pub async fn run() -> Result<()> {
        let cli = Self::parse();

        match cli.command.as_str() {
            "login" | "l" => {
                match cli.site {
                    Site::AtCoder => {
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
                            &["login", cli.site.get_base_url()],
                            Some(&[("USERNAME", &username), ("PASSWORD", &password)])
                        )?;

                        if !output.status.success() {
                            let error = String::from_utf8_lossy(&output.stderr).to_string();
                            return Err(Error::command_failed("oj login", error));
                        }

                        println!("Successfully logged in to AtCoder!");
                    }
                    Site::Codeforces => {
                        return Error::unsupported_feature("Codeforces login");
                    }
                }
            }
            "open" | "o" => {
                // ワークスペースの初期化
                let workspace = Workspace::new(std::env::current_dir()?);

                // 問題を開く
                let source_path = workspace.setup_problem(
                    cli.contest_id.as_ref().unwrap(),
                    cli.problem_id.as_ref().unwrap(),
                    cli.language.unwrap()
                )?;

                // エディタとブラウザで開く
                open_in_editor(&source_path)?;
                open_in_browser(&cli.site.get_problem_url(
                    cli.contest_id.as_ref().unwrap(),
                    cli.problem_id.as_ref().unwrap()
                ))?;
            }
            _ => {
                return Error::invalid_input(format!("invalid command: {}", cli.command));
            }
        }

        Ok(())
    }
}

fn open_in_editor(path: &PathBuf) -> Result<()> {
    for editor in EDITORS {
        if run_command(editor, &[path.to_str().unwrap()], None).is_ok() {
            return Ok(());
        }
    }
    Ok(())
}

fn open_in_browser(url: &str) -> Result<()> {
    open::that(url)?;
    Ok(())
} 