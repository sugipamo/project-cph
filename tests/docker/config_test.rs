use crate::docker::config::{RunnerConfig, LanguageConfig};

#[test]
fn test_runner_config_default() {
    let config = RunnerConfig::default();
    assert_eq!(config.timeout, 10);
    assert_eq!(config.memory_limit, 512);
}

#[test]
fn test_runner_config_custom() {
    let config = RunnerConfig::new(20, 1024);
    assert_eq!(config.timeout, 20);
    assert_eq!(config.memory_limit, 1024);
}

#[test]
fn test_language_config_python() {
    let config = LanguageConfig::from_yaml("src/config/languages.yaml", "python").unwrap();
    assert_eq!(config.image, "python:3.9-slim");
    assert!(config.compile.is_none());
    assert!(!config.needs_compilation());
    assert_eq!(config.compile_dir, "/compile/python");
}

#[test]
fn test_language_config_rust() {
    let config = LanguageConfig::from_yaml("src/config/languages.yaml", "rust").unwrap();
    assert_eq!(config.image, "rust:latest");
    assert!(config.compile.is_some());
    assert!(config.needs_compilation());
    assert_eq!(config.compile_dir, "/compile/rust");
}

#[test]
fn test_language_config_invalid() {
    let result = LanguageConfig::from_yaml("src/config/languages.yaml", "invalid_language");
    assert!(result.is_err());
}

#[test]
fn test_language_config_cpp() {
    let config = LanguageConfig::from_yaml("src/config/languages.yaml", "cpp").unwrap();
    assert_eq!(config.image, "gcc:latest");
    assert!(config.compile.is_some());
    assert!(config.needs_compilation());
    assert_eq!(config.compile_dir, "/compile/cpp");
} 