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
    #[command(alias = "t")]
    Test {
        problem_id: String,
    },

    /// Submit a problem
    #[command(alias = "s")]
    Submit {
        problem_id: String,
    },
}

impl Cli {
    pub fn run() -> Result<()> {
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
        CommonSubCommand::Test { problem_id } => {
            let _test_passed = handle_test(problem_id)?;
            Ok(())
        },
        CommonSubCommand::Submit { problem_id } => handle_submit(problem_id),
    }
}

fn check_login_status(site: Site) -> Result<bool> {
    // oj-toolsのクッキーファイルを確認
    let home_dir = dirs::home_dir()
        .ok_or_else(|| Error::InvalidInput("Could not find home directory".to_string()))?;
    
    let cookie_path = home_dir.join(".local/share/online-judge-tools/cookie.jar");
    if !cookie_path.exists() {
        return Ok(false);
    }

    // サイトへの疎通確認
    let output = run_command(
        "oj",
        &["login", "--check", site.base_url()],
        None
    )?;

    Ok(output.status.success())
}

fn handle_login(site: Site) -> Result<()> {
    // テスト時はログインをスキップ
    if std::env::var("TEST_MODE").is_ok() {
        return Ok(());
    }

    // テグイン状態を確認
    println!("Checking login status for {} ...", site);
    if check_login_status(site)? {
        println!("✓ Already logged in to {}", site);
        return Ok(());
    }

    println!("Login required for {}", site);

    // テスト時は環境変数からユーザー名とパスワードを取得
    let (username, password) = if let (Ok(u), Ok(p)) = (std::env::var("USERNAME"), std::env::var("PASSWORD")) {
        (u, p)
    } else {
        print!("{} username: ", site);
        std::io::Write::flush(&mut std::io::stdout())?;
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

    println!("✓ Successfully logged in to {}!", site);
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

// テストケースのダウンロードを行う共通関数
fn download_test_cases(test_dir: &PathBuf, url: &str, problem_id: &str) -> Result<()> {
    println!("Downloading test cases for problem {} ...", problem_id);
    
    // ログイン状態を確認（サイトはURLから判断）
    let site = Site::from_url(url)?;

    if !check_login_status(site)? {
        println!("⚠ Login required to download test cases");
        handle_login(site)?;
    }
    
    std::fs::create_dir_all(test_dir)?;
    
    let output = run_command(
        "oj",
        &["download", url, "-d", test_dir.to_str().unwrap()],
        None
    )?;

    if output.status.success() {
        println!("✓ Test cases downloaded successfully");
        Ok(())
    } else {
        let error = String::from_utf8_lossy(&output.stderr);
        println!("⚠ Failed to download test cases");
        println!("  Error: {}", error);
        Err(Error::command_failed("oj download", error.into_owned()))
    }
}

// テストケースのダウンロードを確認し、必要に応じてダウンロードする
fn ensure_test_cases(test_dir: &PathBuf, url: &str, problem_id: &str) -> Result<()> {
    if !test_dir.exists() || !has_valid_test_cases(&test_dir)? {
        if let Err(_e) = download_test_cases(test_dir, url, problem_id) {
            println!("  Note: You can still download test cases later with 'test' command");
            // エラーを表示するだけで処理は続行
            Ok(())
        } else {
            Ok(())
        }
    } else {
        println!("✓ Using cached test cases");
        Ok(())
    }
}

fn handle_open(problem_id: String, site: Site) -> Result<()> {
    let (mut workspace, config) = get_workspace_with_config()?;
    let contest_id = config.contest.clone();
    let url = site.problem_url(&contest_id, &problem_id);

    // ソースファイルの作成
    println!("Setting up problem {} ...", problem_id);
    let source_path = workspace.setup_problem(&problem_id)?;
    println!("✓ Problem file created at {}", source_path.display());

    // テラウザで問題ページを開く
    println!("Opening browser and editor ...");
    let output = run_command(
        "python3",
        &["-c", &format!("import webbrowser; webbrowser.open('{}')", url)],
        None
    );

    if let Err(e) = output {
        println!("⚠ Failed to open browser: {}", e);
        println!("  URL: {}", url);
    }

    // エディタでソースファイルを開く
    if let Err(e) = open_in_editor(&source_path) {
        println!("⚠ Failed to open editor: {}", e);
        println!("  Note: You can manually open {}", source_path.display());
    }

    // テストケースのダウンロード
    let test_dir = workspace.get_workspace_dir().join("test").join(&problem_id);
    ensure_test_cases(&test_dir, &url, &problem_id)?;

    Ok(())
}

fn handle_test(problem_id: String) -> Result<bool> {
    let (workspace, config) = get_workspace_with_config()?;
    let source_path = workspace.get_workspace_dir().join(format!("{}.{}", problem_id, config.language.extension()));
    
    if !source_path.exists() {
        return Error::invalid_input(format!("Problem file {} does not exist", source_path.display()));
    }

    println!("Running tests for problem {} ...", problem_id);

    // テストケースのディレクトリを設定
    let test_dir = workspace.get_workspace_dir().join("test").join(&problem_id);
    let url = config.site.problem_url(&config.contest, &problem_id);
    ensure_test_cases(&test_dir, &url, &problem_id)?;

    // テストの実行
    let test_config = crate::Config {
        test_dir,
        problem_file: source_path,
        language: config.language,
    };

    let result = crate::test::run(test_config)?;
    Ok(result)
}

// テストケースが有効かどうかを確認
fn has_valid_test_cases(test_dir: &PathBuf) -> Result<bool> {
    if !test_dir.exists() {
        return Ok(false);
    }

    // 少なくとも1つの.inファイルと対応する.outファイルが存在するか確認
    let entries = std::fs::read_dir(test_dir)?;
    let mut has_input = false;
    let mut has_output = false;

    for entry in entries {
        let entry = entry?;
        let path = entry.path();
        if let Some(ext) = path.extension() {
            if ext == "in" {
                has_input = true;
                let out_path = path.with_extension("out");
                if out_path.exists() {
                    has_output = true;
                    break;
                }
            }
        }
    }

    Ok(has_input && has_output)
}

fn handle_submit(problem_id: String) -> Result<()> {
    let (workspace, config) = get_workspace_with_config()?;
    let workspace_dir = workspace.get_workspace_dir();
    let source_path = workspace_dir.join(format!("{}.{}", problem_id, config.language.extension()));
    
    if !source_path.exists() {
        return Error::invalid_input(format!("Problem file {} does not exist", source_path.display()));
    }

    println!("Running tests before submit...");
    // 提出前にテストを実行
    let test_passed = handle_test(problem_id.clone())?;
    if !test_passed {
        println!("⚠ Tests failed. Do you want to [R]etry, [S]ubmit anyway, or [C]ancel? [R/S/C]");
        let mut input = String::new();
        std::io::stdin().read_line(&mut input)?;
        
        match input.trim().to_lowercase().as_str() {
            "r" => {
                println!("\nRetrying tests...");
                let retry_passed = handle_test(problem_id.clone())?;
                if !retry_passed {
                    println!("⚠ Tests still failing. Submission cancelled.");
                    return Ok(());
                }
            },
            "s" => {
                println!("\nProceeding with submission...");
            },
            "c" => {
                println!("\nSubmission cancelled.");
                return Ok(());
            },
            _ => {
                println!("Invalid input. Submission cancelled.");
                return Ok(());
            }
        }
    }

    println!("\nSubmitting {} ...", problem_id);

    // ログイン状態を確認
    if !check_login_status(config.site)? {
        println!("⚠ Login required to submit");
        handle_login(config.site)?;
    }

    // 提出
    let url = config.site.problem_url(&config.contest, &problem_id);
    println!("Submitting to: {}", url);
    
    // カレントディレクトリを移動
    let current_dir = std::env::current_dir()?;
    std::env::set_current_dir(&workspace_dir)?;
    
    let source_file = format!("{}.{}", problem_id, config.language.extension());
    let language_id = match config.language {
        Language::Rust => "5054", // Rust (rustc 1.70.0)
        Language::PyPy => "5078", // Python (PyPy 3.10-v7.3.12)
    };

    let output = run_command(
        "oj",
        &["submit", "--no-guess", "--wait=0", "--yes", "--language", language_id, &url, &source_file],
        None
    );

    // カレントディレクトリを元に戻す
    std::env::set_current_dir(current_dir)?;
    
    let output = output?;
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    if !output.status.success() {
        println!("⚠ Failed to submit");
        if !stdout.is_empty() {
            println!("Output: {}", stdout);
        }
        if !stderr.is_empty() {
            println!("Error: {}", stderr);
        }
        return Err(Error::command_failed("oj submit", format!("\n{}", stderr)));
    }

    if !stdout.is_empty() {
        println!("{}", stdout);
    }
    println!("✓ Successfully submitted!");
    Ok(())
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

    pub fn from_url(url: &str) -> Result<Self> {
        if url.contains(Self::ATCODER_URL) {
            Ok(Site::AtCoder)
        } else if url.contains(Self::CODEFORCES_URL) {
            Ok(Site::Codeforces)
        } else {
            Err(Error::InvalidInput("Unknown site".to_string()))
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