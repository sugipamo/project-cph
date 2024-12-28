use clap::Parser;
use std::path::{PathBuf, Path};
use crate::{Language, error::Result, workspace::{Workspace, Config}};

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

impl Cli {
    pub async fn execute(self) -> Result<()> {
        self.command.execute().await
    }
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

impl Command {
    pub async fn execute(&self) -> Result<()> {
        match self {
            Command::AtCoder { command } => command.execute().await,
            Command::Codeforces { command } => command.execute().await,
        }
    }
}

#[derive(Parser)]
pub enum CommonSubCommand {
    /// Create a new workspace for a contest
    #[command(name = "new")]
    New {
        /// Contest ID (e.g., abc301)
        contest: String,
    },
    /// Test a problem
    #[command(name = "test")]
    Test {
        /// Problem ID (e.g., a, b, c)
        problem_id: String,
    },
    /// Set programming language
    #[command(name = "language")]
    Language {
        /// Programming language
        #[arg(value_enum)]
        language: Language,
    },
    /// Open a problem
    #[command(name = "open")]
    Open {
        /// Problem ID (e.g., a, b, c)
        problem_id: String,
    },
    /// Submit a problem
    #[command(name = "submit")]
    Submit {
        /// Problem ID (e.g., a, b, c)
        problem_id: String,
    },
    /// Login to the platform
    #[command(name = "login")]
    Login,
}

impl CommonSubCommand {
    pub async fn execute(&self) -> Result<()> {
        match self {
            CommonSubCommand::New { contest } => {
                let mut workspace = Workspace::new()?;
                workspace.set_workspace(contest, Site::AtCoder)?;
                Ok(())
            }
            CommonSubCommand::Test { problem_id } => {
                let workspace = Workspace::new()?;
                let config = workspace.load_config()?;
                let result = run_test(&workspace.get_workspace_dir(), problem_id, &config).await?;
                if result {
                    println!("All tests passed!");
                }
                Ok(())
            }
            CommonSubCommand::Language { language } => {
                let mut workspace = Workspace::new()?;
                workspace.set_language(*language)?;
                println!("Language set to {}", language);
                Ok(())
            }
            CommonSubCommand::Open { problem_id } => {
                let mut workspace = Workspace::new()?;
                let path = workspace.setup_problem(problem_id)?;
                println!("Opening {}", path.display());
                Ok(())
            }
            CommonSubCommand::Submit { problem_id } => {
                let workspace = Workspace::new()?;
                let _config = workspace.load_config()?;
                println!("Submitting problem {}", problem_id);
                Ok(())
            }
            CommonSubCommand::Login => {
                println!("Logging in...");
                Ok(())
            }
        }
    }
}

async fn run_test(workspace_dir: &Path, problem_id: &str, config: &Config) -> Result<bool> {
    let test_dir = workspace_dir.join("test").join(problem_id);
    let source_path = workspace_dir.join(format!("{}.{}", problem_id, config.language.extension()));

    // テストケースの存在確認
    if !has_valid_test_cases(&test_dir)? {
        println!("No test cases found.");
        return Ok(true);
    }

    // テストの実行
    let test_config = Config {
        test_dir,
        problem_file: source_path,
        language: config.language,
        site: config.site,
        contest: config.contest.clone(),
    };

    crate::test::run(test_config).await
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