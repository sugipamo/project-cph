use cph::cli::{Cli, Commands, commands::{create_command, CommandContext}};
use clap::Parser;
use std::env;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    // コマンドのコンテキストを作成
    let context = CommandContext {
        site: cli.site,
        workspace_path: env::current_dir()?,
    };

    // コマンドを作成して実行
    match &cli.command {
        Commands::Work { contest_id } => {
            if let Some(command) = create_command("work", context) {
                command.execute(&cli.command)?;
            }
        }
        Commands::Test { problem_id } => {
            if let Some(command) = create_command("test", context) {
                command.execute(&cli.command)?;
            }
        }
        Commands::Language { language } => {
            if let Some(command) = create_command("language", context) {
                command.execute(&cli.command)?;
            }
        }
        Commands::Open { problem_id } => {
            if let Some(command) = create_command("open", context) {
                command.execute(&cli.command)?;
            }
        }
        Commands::Submit { problem_id } => {
            if let Some(command) = create_command("submit", context) {
                command.execute(&cli.command)?;
            }
        }
        Commands::Generate { problem_id } => {
            if let Some(command) = create_command("generate", context) {
                command.execute(&cli.command)?;
            }
        }
        Commands::Login => {
            if let Some(command) = create_command("login", context) {
                command.execute(&cli.command)?;
            }
        }
    }

    Ok(())
}
