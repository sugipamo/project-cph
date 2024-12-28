use cph::cli::Cli;
use clap::Parser;

#[tokio::main]
async fn main() -> cph::error::Result<()> {
    let cli = Cli::parse();
    cli.execute().await
}
