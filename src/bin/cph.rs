use cph::config::Config;
use std::error::Error;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let _config = Config::load()?;
    Ok(())
}
