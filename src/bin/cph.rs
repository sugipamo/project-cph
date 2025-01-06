use cph::config::Config;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let _config = Config::new()?;
    Ok(())
}
