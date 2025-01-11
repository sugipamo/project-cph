use std::env;
use anyhow::Result;
use cph::config::Config;

#[test]
fn test_yaml_merge() -> Result<()> {
    let yaml = r#"
base: &base
  name: "base"
  value: 1
  nested:
    key: "original"

extended:
  <<: *base
  value: 2
  nested:
    key: "override"
"#;
    
    let config = Config::parse_str(yaml)?;
    
    assert_eq!(config.get::<String>("extended.name")?, "base");
    assert_eq!(config.get::<i64>("extended.value")?, 2);
    assert_eq!(config.get::<String>("extended.nested.key")?, "override");
    
    Ok(())
}

#[test]
fn test_env_var_expansion() -> Result<()> {
    env::set_var("TEST_VAR", "env_value");
    
    let yaml = r#"
test:
  value1: "${TEST_VAR-default}"
  value2: "${NONEXISTENT-default}"
"#;
    
    let config = Config::parse_str(yaml)?;
    
    assert_eq!(config.get::<String>("test.value1")?, "env_value");
    assert_eq!(config.get::<String>("test.value2")?, "default");
    
    env::remove_var("TEST_VAR");
    Ok(())
}

#[test]
fn test_config_file_not_found() {
    let result = Config::from_file("nonexistent.yaml");
    assert!(result.is_err());
}

#[test]
fn test_invalid_yaml() {
    let yaml = "invalid: : yaml";
    let result = Config::parse_str(yaml);
    assert!(result.is_err());
}

#[test]
fn test_non_mapping_root() {
    let yaml = "- just\n- a\n- sequence";
    let result = Config::parse_str(yaml);
    assert!(result.is_err());
}

#[test]
fn test_path_not_found() {
    let yaml = "key: value";
    let config = Config::parse_str(yaml).unwrap();
    let result: Result<String> = config.get("nonexistent.path");
    assert!(result.is_err());
}

#[test]
fn test_type_mismatch() {
    let yaml = "number: not_a_number";
    let config = Config::parse_str(yaml).unwrap();
    let result: Result<i64> = config.get("number");
    assert!(result.is_err());
} 