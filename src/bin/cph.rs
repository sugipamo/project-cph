use cph::cli::Command;

#[tokio::main]
async fn main() -> cph::error::Result<()> {
    Command::run().await
}
