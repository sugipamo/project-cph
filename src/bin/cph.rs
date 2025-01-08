use std::env;
use anyhow::{Context, Result};
use cph::config::Config;

fn main() -> Result<()> {
    if env::args().nth(1).is_none() {
        println!("Usage: cph <command> [args...]");
        return Ok(());
    }

    let _config = Config::load_from_file("src/config/config.yaml")
        .with_context(|| "src/config/config.yamlの読み込みに失敗しました")?;
    Ok(())
}
