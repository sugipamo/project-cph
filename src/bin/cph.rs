use cph::config::Config;
use serde_yaml::Value;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let root_value = Value::Mapping(serde_yaml::Mapping::new());
    let _config = Config::new(root_value);
    Ok(())
}
