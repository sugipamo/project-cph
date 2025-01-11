use std::env;
use anyhow::Result;
use cph::config::Config;

fn main() -> Result<()> {
    if env::args().nth(1).is_none() {
        println!("Usage: cph <command> [args...]");
        return Ok(());
    }

    let _config = Config::from_file("src/config/config.yaml")?;
    Ok(())
}
