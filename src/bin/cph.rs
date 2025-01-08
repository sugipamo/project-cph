use std::env;
use anyhow::{Context, Result};
use cph::Config;

fn main() -> Result<()> {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.is_empty() {
        return Ok(());
    }

    let _config = Config::load_from_file("src/config/config.yaml")
        .with_context(|| "src/config/config.yamlの読み込みに失敗しました")?;

    Ok(())
}
