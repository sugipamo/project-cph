use cph::cli::{Cli, Commands, commands::{create_command, CommandContext}};
use clap::Parser;
use std::env;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    // コマンドのコンテキストを作成
    let context = CommandContext {
        site: cli.site,
        active_contest_dir: env::current_dir()?,
    };

    // コマンドを作成して実行
    match &cli.command {
        // 引数を使用するコマンドは、create_commandに渡すことで
        // 実際の処理がコマンドクラスに委譲されることを示す
        Commands::Work { .. } => execute_command("work", &cli.command, context).await?,
        Commands::Test { .. } => execute_command("test", &cli.command, context).await?,
        Commands::Language { .. } => execute_command("language", &cli.command, context).await?,
        Commands::Open { .. } => execute_command("open", &cli.command, context).await?,
        Commands::Submit { .. } => execute_command("submit", &cli.command, context).await?,
        Commands::Generate { .. } => execute_command("generate", &cli.command, context).await?,
        Commands::Login => execute_command("login", &cli.command, context).await?,
    }

    Ok(())
}

/// コマンドを作成して実行する
/// 
/// # エラーハンドリング
/// - コマンドの実行に失敗した場合は、エラーを返す
/// - 軽微なエラーは各コマンド内で処理され、`println!`で報告される
async fn execute_command(
    command_type: &str,
    command: &Commands,
    context: CommandContext,
) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(command_handler) = create_command(command_type, context) {
        command_handler.execute(command).await?;
    }
    Ok(())
}
