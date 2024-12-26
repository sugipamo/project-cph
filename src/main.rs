use cph::cli::Cli;

#[tokio::main]
async fn main() -> cph::error::Result<()> {
    Cli::run().await
}
