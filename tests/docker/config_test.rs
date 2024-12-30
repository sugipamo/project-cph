use cph::docker::{RunnerConfig, LanguageConfig};

#[test]
fn test_runner_config_default() {
    let config = RunnerConfig::default();
    assert_eq!(config.timeout_seconds, 10);
    assert_eq!(config.memory_limit_mb, 512);
    assert_eq!(config.mount_point, "/compile");
}

#[test]
fn test_runner_config_custom() {
    let config = RunnerConfig::new(20, 1024, "/test".to_string());
    assert_eq!(config.timeout_seconds, 20);
    assert_eq!(config.memory_limit_mb, 1024);
    assert_eq!(config.mount_point, "/test");
}

#[test]
fn test_runner_config_from_yaml() {
    let config = RunnerConfig::from_yaml("src/config/docker.yaml").unwrap();
    assert_eq!(config.timeout_seconds, 5);
    assert_eq!(config.memory_limit_mb, 128);
    assert_eq!(config.mount_point, "/compile");
}

#[test]
fn test_python_config() {
    let config = LanguageConfig::from_yaml("src/config/languages.yaml", "python").unwrap();
    assert_eq!(config.runner.image, "python:3.9-slim");
    assert!(config.runner.compile.is_none());
    assert!(!config.runner.needs_compilation());
    assert_eq!(config.runner.compile_dir, "compile/python");
}

#[test]
fn test_rust_config() {
    let config = LanguageConfig::from_yaml("src/config/languages.yaml", "rust").unwrap();
    assert_eq!(config.runner.image, "rust:latest");
    assert!(config.runner.compile.is_some());
    assert!(config.runner.needs_compilation());
    assert_eq!(config.runner.compile_dir, "compile/rust");
}

#[test]
fn test_invalid_language() {
    let result = LanguageConfig::from_yaml("src/config/languages.yaml", "invalid_language");
    assert!(result.is_err());
}

#[test]
fn test_cpp_config() {
    let config = LanguageConfig::from_yaml("src/config/languages.yaml", "cpp").unwrap();
    assert_eq!(config.runner.image, "gcc:latest");
    assert!(config.runner.compile.is_some());
    assert!(config.runner.needs_compilation());
    assert_eq!(config.runner.compile_dir, "compile/cpp");
} 