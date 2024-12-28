use std::path::{Path, PathBuf};
use clap::{Parser, Subcommand};
use serde::{Serialize, Deserialize};
use crate::{Language, error::Result, workspace::{Workspace, Config}};

#[derive(Debug, Parser)]
#[command(name = "cph")]
pub struct Cli {
    #[command(subcommand)]
    pub site: Site,
}

#[derive(Debug, Subcommand, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Site {
    #[command(name = "atcoder", alias = "at-coder", alias = "at_coder")]
    AtCoder {
        #[command(subcommand)]
        command: CommonSubCommand,
    },
}

#[derive(Debug, Subcommand, Clone, Serialize, Deserialize)]
pub enum CommonSubCommand {
    #[command(name = "work", alias = "w")]
    Work {
        contest: String,
    },
    #[command(name = "test", alias = "t")]
    Test {
        problem_id: String,
    },
    #[command(name = "language", alias = "l")]
    Language {
        language: Language,
    },
    #[command(name = "open", alias = "o")]
    Open {
        problem_id: String,
    },
    #[command(name = "submit", alias = "s")]
    Submit {
        problem_id: String,
    },
    #[command(name = "generate", alias = "g")]
    Generate {
        problem_id: String,
    },
    #[command(name = "login")]
    Login,
}

impl Cli {
    pub async fn execute(self) -> Result<()> {
        match self.site {
            Site::AtCoder { command } => command.execute().await,
        }
    }
}

impl CommonSubCommand {
    pub async fn execute(&self) -> Result<()> {
        match self {
            CommonSubCommand::Work { contest } => {
                let mut workspace = Workspace::new()?;
                let current_contest = workspace.get_current_config().map(|c| c.contest.clone()).unwrap_or_default();
                if !current_contest.is_empty() && current_contest == *contest {
                    println!("Already in contest {}", contest);
                    return Ok(());
                }
                workspace.set_workspace(contest, Site::AtCoder { command: CommonSubCommand::Work { contest: contest.clone() } })?;
                println!("Successfully set up workspace for contest {}", contest);
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
            CommonSubCommand::Generate { problem_id: _ } => {
                println!("Generate command is not implemented yet");
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
    let workspace = Workspace::new()?;
    let test_dir = workspace.get_test_dir(problem_id);

    // テストケースの存在確認
    if !has_valid_test_cases(&test_dir)? {
        println!("No test cases found.");
        return Ok(true);
    }

    // テストの実行
    let test_config = Config {
        language: config.language,
        site: config.site.clone(),
        contest: config.contest.clone(),
    };

    crate::test::run(test_config, problem_id).await
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
        if let Some(extension) = path.extension() {
            if extension == "in" {
                has_input = true;
            } else if extension == "out" {
                has_output = true;
            }
        }
    }

    Ok(has_input && has_output)
} 