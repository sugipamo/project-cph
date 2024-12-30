use clap::Parser;
use cph::cli::Cli;

#[tokio::main]
async fn main() -> cph::error::Result<()> {
    let cli = Cli::parse();
    cli.execute().await
}
