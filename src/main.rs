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

use application::{TestService, OpenService, SubmitService};
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
    open_service: Arc<OpenService>,
    submit_service: Arc<SubmitService>,
}

impl AppContainer {
    fn new() -> Result<Self> {
        let file_system: Arc<dyn FileSystem> = Arc::new(LocalFileSystem::new());
        let shell: Arc<dyn Shell> = Arc::new(SystemShell::new());
        let test_runner: Arc<dyn TestRunner> = Arc::new(LocalTestRunner::new(shell.clone()));
        let test_service = Arc::new(TestService::new(file_system.clone(), test_runner.clone()));
        let open_service = Arc::new(OpenService::new(file_system.clone(), shell.clone()));
        let submit_service = Arc::new(SubmitService::new(file_system.clone(), shell.clone()));
        
        Ok(Self {
            file_system,
            shell,
            test_runner,
            test_service,
            open_service,
            submit_service,
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
            if let Some(ref url) = url {
                tracing::info!("URL: {}", url);
            }
            container.open_service.open_problem(name, url).await
        }
        Commands::Submit { problem, file } => {
            tracing::info!("Submitting solution for problem: {}", problem);
            container.submit_service.submit_solution(problem, file).await
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
            eprintln!("このコマンドはまだ実装されていません。");
            eprintln!("initコマンドは競技プログラミング用のワークスペースを初期化します。");
            eprintln!("\n手動でセットアップする場合:");
            eprintln!("  1. プロジェクトディレクトリを作成");
            eprintln!("  2. 言語固有の設定ファイルを作成 (Cargo.toml, package.json等)");
            eprintln!("  3. テンプレートファイルを準備");
            eprintln!("\n今後、このコマンドは自動的にこれらの作業を行います。");
            Err(anyhow::anyhow!("コマンドが未実装です"))
        }
    };

    // Handle errors with user-friendly messages
    if let Err(e) = result {
        eprintln!("エラー: {}", e);
        
        // コンテキストに応じた追加のヘルプメッセージ
        if e.to_string().contains("問題ディレクトリ") && e.to_string().contains("見つかりません") {
            eprintln!("\nヒント: 'cph open <問題名>' で問題を開いてから実行してください。");
        } else if e.to_string().contains("ファイルが見つかりません") {
            eprintln!("\nヒント: ファイルパスが正しいか確認してください。");
        } else if e.to_string().contains("Some tests failed") {
            eprintln!("\nヒント: 失敗したテストケースの詳細を確認して、コードを修正してください。");
        }
        
        std::process::exit(1);
    }

    Ok(())
}