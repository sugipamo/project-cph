use std::path::{Path, PathBuf};
use clap::{Parser, Subcommand};
use serde::{Serialize, Deserialize};
use crate::{Language, error::Result, workspace::{Workspace, Config}, oj::OJContainer, oj::ProblemInfo};

#[derive(Debug, Parser)]
#[command(name = "cph")]
pub struct Cli {
    #[command(subcommand)]
    pub site: Site,
}

#[derive(Debug, Subcommand, Clone)]
pub enum Site {
    #[command(name = "atcoder", alias = "at-coder", alias = "at_coder")]
    AtCoder {
        #[command(subcommand)]
        command: CommonSubCommand,
    },
}

impl From<&str> for Site {
    fn from(s: &str) -> Self {
        match s {
            "atcoder" => Site::AtCoder { command: default_command() },
            _ => panic!("Unknown site: {}", s),
        }
    }
}

impl<'de> Deserialize<'de> for Site {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        Ok(Site::from(s.as_str()))
    }
}

impl Serialize for Site {
    fn serialize<S>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        match self {
            Site::AtCoder { .. } => serializer.serialize_str("atcoder"),
        }
    }
}

fn default_command() -> CommonSubCommand {
    CommonSubCommand::Work { contest: String::new() }
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
                let config = workspace.load_config()?;
                
                // 問題URLの生成
                let url = format!(
                    "https://atcoder.jp/contests/{}/tasks/{}_{}",
                    config.contest,
                    config.contest,
                    problem_id
                );

                // ソースファイルの準備
                let path = workspace.setup_problem(problem_id)?;
                
                // テストケースのダウンロード
                let oj = OJContainer::new(workspace.get_workspace_dir())?;
                oj.ensure_image().await?;
                
                let problem = ProblemInfo {
                    url: url.clone(),
                    source_path: path.clone(),
                    problem_id: problem_id.to_string(),
                };
                
                oj.open(problem).await?;
                
                println!("Problem setup completed for {}", path.display());
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

async fn run_test(_workspace_dir: &Path, problem_id: &str, config: &Config) -> Result<bool> {
    let mut workspace = Workspace::new()?;
    let problem_path = workspace.setup_problem(problem_id)?;

    // テストケースの存在確認
    if !has_valid_test_cases(&problem_path)? {
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
fn has_valid_test_cases(problem_dir: &PathBuf) -> Result<bool> {
    if !problem_dir.exists() {
        return Ok(false);
    }

    // 少なくとも1つの.inファイルと対応する.outファイルが存在するか確認
    let entries = std::fs::read_dir(problem_dir)?;
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