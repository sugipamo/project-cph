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

#[test]
fn test_nested_merge() -> Result<()> {
    let yaml = r#"
base: &base
  deep:
    nested:
      value: 1
      keep: true
    array: [1, 2, 3]

extended:
  <<: *base
  deep:
    nested:
      value: 2
    array: [4, 5]
"#;
    
    let config = Config::parse_str(yaml)?;
    
    assert_eq!(config.get::<i64>("extended.deep.nested.value")?, 2);
    assert_eq!(config.get::<bool>("extended.deep.nested.keep")?, true);
    assert_eq!(config.get::<Vec<i64>>("extended.deep.array")?, vec![4, 5]);
    
    Ok(())
}

#[test]
fn test_multiple_env_vars() -> Result<()> {
    env::set_var("TEST_VAR1", "value1");
    env::set_var("TEST_VAR2", "value2");
    
    let yaml = r#"
test:
  combined: "${TEST_VAR1}-${TEST_VAR2}"
  nested:
    env: "${TEST_VAR1}"
    default: "${NONEXISTENT-${TEST_VAR2}}"
"#;
    
    let config = Config::parse_str(yaml)?;
    
    assert_eq!(config.get::<String>("test.combined")?, "value1-value2");
    assert_eq!(config.get::<String>("test.nested.env")?, "value1");
    assert_eq!(config.get::<String>("test.nested.default")?, "value2");
    
    env::remove_var("TEST_VAR1");
    env::remove_var("TEST_VAR2");
    Ok(())
}

#[test]
fn test_type_conversions() -> Result<()> {
    let yaml = r#"
values:
  string: "123"
  int: 123
  float: 123.45
  bool_true: true
  bool_string: "true"
"#;
    
    let config = Config::parse_str(yaml)?;
    
    assert_eq!(config.get::<String>("values.string")?, "123");
    assert_eq!(config.get::<i64>("values.string")?, 123);
    assert_eq!(config.get::<i64>("values.int")?, 123);
    assert_eq!(config.get::<f64>("values.float")?, 123.45);
    assert_eq!(config.get::<bool>("values.bool_true")?, true);
    assert_eq!(config.get::<bool>("values.bool_string")?, true);
    
    Ok(())
}

#[test]
fn test_array_access() -> Result<()> {
    let yaml = r#"
arrays:
  simple: [1, 2, 3]
  nested:
    - name: "item1"
      value: 1
    - name: "item2"
      value: 2
"#;
    
    let config = Config::parse_str(yaml)?;
    
    assert_eq!(config.get::<Vec<i64>>("arrays.simple")?, vec![1, 2, 3]);
    assert_eq!(config.get::<String>("arrays.nested[0].name")?, "item1");
    assert_eq!(config.get::<i64>("arrays.nested[1].value")?, 2);
    
    Ok(())
}

#[test]
fn test_complex_defaults() -> Result<()> {
    let yaml = r#"
defaults:
  value1: "${ENV1-${ENV2-${ENV3-default}}}"
  value2: "${ENV1-prefix_${ENV2-middle}_${ENV3-suffix}}"
"#;
    
    let config = Config::parse_str(yaml)?;
    
    assert_eq!(config.get::<String>("defaults.value1")?, "default");
    assert_eq!(config.get::<String>("defaults.value2")?, "prefix_middle_suffix");
    
    Ok(())
} 