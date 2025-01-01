use clap::Parser;
use cph::cli::{Cli, Commands};
use cph::cli::commands::{Command, CommandContext};
use cph::config::Config;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    // 設定を読み込む
    let config = Config::load()?;

    // コマンドコンテキストを作成
    let context = match &cli.command {
        Commands::Work { contest_id } => CommandContext {
            problem_id: contest_id.clone(),
        },
        Commands::Test { problem_id } => CommandContext {
            problem_id: problem_id.clone(),
        },
        Commands::Language { language } => CommandContext {
            problem_id: language.clone(),
        },
        Commands::Open { problem_id } => CommandContext {
            problem_id: problem_id.clone(),
        },
        Commands::Submit { problem_id } => CommandContext {
            problem_id: problem_id.clone(),
        },
        Commands::Generate { problem_id } => CommandContext {
            problem_id: problem_id.clone(),
        },
        Commands::Login => CommandContext {
            problem_id: String::new(),
        },
    };

    // コマンドを生成して実行
    if let Some(command) = cph::cli::commands::create_command(cli.command.as_str(), context) {
        command.execute(&cli.command).await?;
    }

    Ok(())
}
