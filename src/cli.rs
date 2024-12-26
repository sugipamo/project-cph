use clap::Parser;
use std::path::PathBuf;
use crate::{Language, error::{Result, Error}, workspace::Workspace};
use std::process::Command as StdCommand;
use std::process::Output;

const EDITORS: &[&str] = &["code", "cursor"];

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
pub struct Cli {
    /// Site name (e.g., atcoder, codeforces)
    #[arg(value_enum)]
    site: Site,

    /// Command to execute (login/l, open/o, test/t, submit/s, generate/g)
    #[arg(value_parser = parse_command)]
    command: String,

    /// Contest ID (e.g., abc001) - Required for open command
    #[arg(required_if_eq("command", "open"))]
    contest_id: Option<String>,

    /// Programming language (rust/r or pypy/py) - Required for open command
    #[arg(value_enum)]
    #[arg(required_if_eq("command", "open"))]
    language: Option<Language>,

    /// Problem ID (e.g., a, b, c) - Required for open and test/submit/generate commands
    #[arg(required_if_eq("command", "open"))]
    #[arg(required_if_eq("command", "test"))]
    #[arg(required_if_eq("command", "submit"))]
    #[arg(required_if_eq("command", "generate"))]
    problem_id: Option<String>,
}

fn parse_command(s: &str) -> std::result::Result<String, String> {
    match s {
        "login" | "l" | "open" | "o" | "test" | "t" | "submit" | "s" | "generate" | "g" => Ok(s.to_string()),
        _ => Err(format!("invalid command: '{}'. Valid commands are: login (l), open (o), test (t), submit (s), generate (g)", s))
    }
}

#[derive(Debug, Clone, Copy, clap::ValueEnum, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Site {
    #[clap(name = "atcoder", alias = "at-coder", alias = "at_coder")]
    AtCoder,
    #[clap(name = "codeforces", alias = "cf")]
    Codeforces,
}

impl Cli {
    fn get_required_args(&self) -> Result<(&str, &str, Language)> {
        let contest_id = self.contest_id.as_ref()
            .ok_or_else(|| Error::InvalidInput("Contest ID is required for this command".to_string()))?;
        let problem_id = self.problem_id.as_ref()
            .ok_or_else(|| Error::InvalidInput("Problem ID is required for this command".to_string()))?;
        let language = self.language
            .ok_or_else(|| Error::InvalidInput("Language is required for this command".to_string()))?;
        
        Ok((contest_id, problem_id, language))
    }

    pub async fn run() -> Result<()> {
        let cli = Self::parse();

        match cli.command.as_str() {
            "login" | "l" => {
                // ログインコマンドの処理
                if cli.contest_id.is_some() || cli.problem_id.is_some() || cli.language.is_some() {
                    return Err(Error::InvalidInput("login command does not accept contest_id, problem_id, or language arguments".to_string()));
                }
                match cli.site {
                    Site::AtCoder => {
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
                    Site::Codeforces => {
                        Error::unsupported_feature("Codeforces login")?
                    }
                }
            }
            "open" | "o" => {
                let (contest_id, problem_id, language) = cli.get_required_args()?;
                
                // ワークスペースの初期化
                let mut workspace = Workspace::new(std::env::current_dir()?);

                // 問題を開く
                let source_path = workspace.setup_problem(
                    contest_id,
                    problem_id,
                    language,
                    cli.site
                )?;

                // エディタとブラウザで開く
                open_in_editor(&source_path)?;
                open_in_browser(&cli.site.problem_url(contest_id, problem_id))?;
            }
            "test" | "t" | "submit" | "s" | "generate" | "g" => {
                Error::unsupported_feature(&format!("{} command", cli.command))?
            }
            _ => {
                return Err(Error::InvalidInput(format!("invalid command: {}", cli.command)));
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