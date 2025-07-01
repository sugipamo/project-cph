#![allow(dead_code)]

use anyhow::{Context, Result}; 
use clap::{Parser, Subcommand};
use std::sync::Arc;
use std::path::PathBuf;

mod interfaces;
mod infrastructure;
mod application;
mod domain;
mod errors;

use application::TestService;
use infrastructure::drivers::{file_system::LocalFileSystem, shell::SystemShell, test_runner::LocalTestRunner};
use interfaces::file_system::FileSystem;
use interfaces::shell::Shell;
use interfaces::test_runner::TestRunner;

#[derive(Parser)]
#[command(name = "cph")]
#[command(about = "Competitive Programming Helper", long_about = None)]
#[command(version)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Open a new problem
    Open {
        /// The name of the problem
        name: String,
        /// The URL of the problem (optional)
        #[arg(short, long)]
        url: Option<String>,
    },
    /// Submit a solution
    Submit {
        /// The problem name
        problem: String,
        /// The solution file path
        #[arg(short, long)]
        file: Option<String>,
    },
    /// Run tests for a problem
    Test {
        /// The problem directory path (optional, defaults to current directory)
        path: Option<PathBuf>,
    },
    /// Initialize a new workspace
    Init,
}

struct AppContainer {
    file_system: Arc<dyn FileSystem>,
    shell: Arc<dyn Shell>,
    test_runner: Arc<dyn TestRunner>,
    test_service: Arc<TestService>,
}

impl AppContainer {
    fn new() -> Result<Self> {
        let file_system: Arc<dyn FileSystem> = Arc::new(LocalFileSystem::new());
        let shell: Arc<dyn Shell> = Arc::new(SystemShell::new());
        let test_runner: Arc<dyn TestRunner> = Arc::new(LocalTestRunner::new(shell.clone()));
        let test_service = Arc::new(TestService::new(file_system.clone(), test_runner.clone()));
        
        Ok(Self {
            file_system,
            shell,
            test_runner,
            test_service,
        })
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    // Parse CLI arguments
    let cli = Cli::parse();

    // Initialize dependency container
    let container = AppContainer::new()
        .context("Failed to initialize application container")?;

    // Handle commands with proper error handling
    let result: Result<()> = match cli.command {
        Commands::Open { name, url } => {
            tracing::info!("Opening problem: {}", name);
            if let Some(url) = url {
                tracing::info!("URL: {}", url);
            }
            // TODO: Implement open command
            Ok(())
        }
        Commands::Submit { problem, file: _ } => {
            tracing::info!("Submitting solution for problem: {}", problem);
            // TODO: Implement submit command
            Ok(())
        }
        Commands::Test { path } => {
            tracing::info!("Running tests for problem in: {:?}", path.as_ref().unwrap_or(&PathBuf::from(".")));
            
            let results = container.test_service.run_tests(path).await?;
            
            // Display results
            for result in &results {
                match &result.status {
                    domain::test_case::TestStatus::Passed => {
                        println!("✓ Test '{}' passed ({}ms)", result.test_case.name, result.execution_time_ms);
                    }
                    domain::test_case::TestStatus::Failed { reason } => {
                        println!("✗ Test '{}' failed ({}ms)", result.test_case.name, result.execution_time_ms);
                        println!("  {}", reason);
                    }
                    domain::test_case::TestStatus::RuntimeError { message } => {
                        println!("✗ Test '{}' runtime error: {}", result.test_case.name, message);
                    }
                    domain::test_case::TestStatus::CompilationError { message } => {
                        println!("✗ Compilation error: {}", message);
                        break;
                    }
                    domain::test_case::TestStatus::TimeLimitExceeded => {
                        println!("✗ Test '{}' time limit exceeded", result.test_case.name);
                    }
                }
            }
            
            let passed = results.iter().filter(|r| matches!(r.status, domain::test_case::TestStatus::Passed)).count();
            let total = results.len();
            println!("\nPassed {}/{} tests", passed, total);
            
            if passed < total {
                return Err(anyhow::anyhow!("Some tests failed"));
            }
            
            Ok(())
        }
        Commands::Init => {
            tracing::info!("Initializing workspace");
            // TODO: Implement init command
            Ok(())
        }
    };

    // Handle errors with user-friendly messages
    if let Err(e) = result {
        eprintln!("Error: {}", e);
        std::process::exit(1);
    }

    Ok(())
}