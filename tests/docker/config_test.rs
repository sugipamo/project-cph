#[cfg(feature = "docker_test")]
use super::get_test_config_path;
#[cfg(feature = "docker_test")]
use cph::docker::config::RunnerConfig;

#[cfg(feature = "docker_test")]
#[tokio::test]
async fn test_load_config() {
    let config = RunnerConfig::load(get_test_config_path()).unwrap();
    assert_eq!(config.timeout_seconds, 5);
    assert_eq!(config.memory_limit_mb, 128);
}

#[cfg(feature = "docker_test")]
#[tokio::test]
async fn test_get_language_config() {
    let config = RunnerConfig::load(get_test_config_path()).unwrap();
    
    // Python設定のテスト
    let python_config = config.get_language_config("python").unwrap();
    assert_eq!(python_config.image_name, "python:3.9-slim");
    assert!(python_config.compile_cmd.is_none());
    assert_eq!(python_config.run_cmd, vec!["python", "-u", "-c"]);
    assert_eq!(python_config.workspace_dir, "/compile/python");
    
    // PyPy設定のテスト
    let pypy_config = config.get_language_config("pypy").unwrap();
    assert_eq!(pypy_config.image_name, "pypy:3.9-slim");
    assert!(pypy_config.compile_cmd.is_none());
    assert_eq!(pypy_config.run_cmd, vec!["pypy3", "-u", "-c"]);
    assert_eq!(pypy_config.workspace_dir, "/compile/pypy");
    
    // C++設定のテスト
    let cpp_config = config.get_language_config("cpp").unwrap();
    assert_eq!(cpp_config.image_name, "gcc:latest");
    assert_eq!(cpp_config.compile_cmd.as_ref().unwrap(), &vec!["g++", "-std=c++17", "-O2", "main.cpp"]);
    assert_eq!(cpp_config.workspace_dir, "/compile/cpp");
    
    // Rust設定のテスト
    let rust_config = config.get_language_config("rust").unwrap();
    assert_eq!(rust_config.image_name, "rust:latest");
    assert_eq!(rust_config.compile_cmd.as_ref().unwrap(), &vec!["rustc", "main.rs"]);
    assert_eq!(rust_config.workspace_dir, "/compile/rust");
}

#[cfg(feature = "docker_test")]
#[tokio::test]
async fn test_validate_language() {
    let config = RunnerConfig::load(get_test_config_path()).unwrap();
    
    // 有効な言語
    assert!(config.validate_language("python").is_ok());
    assert!(config.validate_language("pypy").is_ok());
    assert!(config.validate_language("cpp").is_ok());
    assert!(config.validate_language("rust").is_ok());
    
    // 無効な言語
    assert!(config.validate_language("invalid").is_err());
} 