#![allow(dead_code)]

use anyhow::Result;
use clap::{Parser, Subcommand};
// use std::sync::Arc; // Will be used when we implement dependency injection

mod interfaces;
mod infrastructure;
mod application;
mod domain;

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
        /// The problem name
        problem: String,
    },
    /// Initialize a new workspace
    Init,
}

struct AppContainer {
    // Infrastructure dependencies will be injected here
    // file_system: Arc<dyn interfaces::file_system::FileSystem>,
    // shell: Arc<dyn interfaces::shell::Shell>,
    // logger: Arc<dyn interfaces::logger::Logger>,
    // config: Arc<dyn interfaces::config::ConfigProvider>,
}

impl AppContainer {
    fn new() -> Result<Self> {
        // TODO: Initialize infrastructure components
        Ok(Self {})
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
    let _container = AppContainer::new()?;

    // Handle commands
    match cli.command {
        Commands::Open { name, url } => {
            tracing::info!("Opening problem: {}", name);
            if let Some(url) = url {
                tracing::info!("URL: {}", url);
            }
            // TODO: Implement open command
        }
        Commands::Submit { problem, file: _ } => {
            tracing::info!("Submitting solution for problem: {}", problem);
            // TODO: Implement submit command
        }
        Commands::Test { problem } => {
            tracing::info!("Running tests for problem: {}", problem);
            // TODO: Implement test command
        }
        Commands::Init => {
            tracing::info!("Initializing workspace");
            // TODO: Implement init command
        }
    }

    Ok(())
}