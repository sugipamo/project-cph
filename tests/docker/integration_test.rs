use std::process::Command;
use std::path::PathBuf;
use std::fs;
use cph::config::Config;
use cph::docker::{DockerRunner, DockerError};

// テストヘルパー
struct IntegrationTestContext {
    temp_dir: PathBuf,
}

impl IntegrationTestContext {
    fn new() -> Self {
        let temp_dir = std::env::temp_dir().join("cph-test");
        fs::create_dir_all(&temp_dir).unwrap();
        Self { temp_dir }
    }

    fn cleanup(&self) {
        let _ = fs::remove_dir_all(&self.temp_dir);
    }
}

impl Drop for IntegrationTestContext {
    fn drop(&mut self) {
        self.cleanup();
    }
}

// Dockerデーモンが利用可能かチェックする
fn check_docker_available() -> bool {
    Command::new("docker")
        .arg("info")
        .output()
        .map(|output| output.status.success())
        .unwrap_or(false)
}

#[tokio::test]
async fn test_docker_available() {
    assert!(check_docker_available(), "Dockerが利用できません");
}

#[tokio::test]
async fn test_rust_simple_program() {
    let _ctx = IntegrationTestContext::new();
    let config = Config::load().unwrap();
    let mut runner = DockerRunner::new(config, "rust".to_string()).unwrap();

    let source_code = r#"
        fn main() {
            println!("Hello from Rust!");
        }
    "#;

    let result = runner.run_in_docker(source_code).await;
    assert!(result.is_ok());
    assert!(result.unwrap().contains("Hello from Rust!"));
}

#[tokio::test]
async fn test_timeout_handling() {
    let _ctx = IntegrationTestContext::new();
    let config = Config::load().unwrap();
    let mut runner = DockerRunner::new(config, "rust".to_string()).unwrap();

    let source_code = r#"
        fn main() {
            loop {}
        }
    "#;

    match runner.run_in_docker(source_code).await {
        Ok(_) => panic!("タイムアウトが発生しませんでした"),
        Err(e) => match e {
            DockerError::Timeout(_) => (),
            _ => panic!("予期しないエラー: {}", e),
        },
    }
}

#[tokio::test]
async fn test_memory_limit() {
    let _ctx = IntegrationTestContext::new();
    let config = Config::load().unwrap();
    let mut runner = DockerRunner::new(config, "rust".to_string()).unwrap();

    let source_code = r#"
        fn main() {
            let mut v = Vec::new();
            loop {
                v.extend(vec![1; 1024 * 1024]); // 1MB
            }
        }
    "#;

    match runner.run_in_docker(source_code).await {
        Ok(_) => panic!("メモリ制限が機能していません"),
        Err(e) => match e {
            DockerError::Memory(_) | DockerError::Runtime(_) => (),
            _ => panic!("予期しないエラー: {}", e),
        },
    }
}

#[tokio::test]
async fn test_multiple_languages() {
    let _ctx = IntegrationTestContext::new();
    let config = Config::load().unwrap();

    // Rust
    let mut rust_runner = DockerRunner::new(config.clone(), "rust".to_string()).unwrap();
    let rust_code = r#"fn main() { println!("Rust"); }"#;
    let rust_result = rust_runner.run_in_docker(rust_code).await;
    assert!(rust_result.is_ok());
    assert!(rust_result.unwrap().contains("Rust"));

    // Python
    let mut python_runner = DockerRunner::new(config.clone(), "python".to_string()).unwrap();
    let python_code = r#"print("Python")"#;
    let python_result = python_runner.run_in_docker(python_code).await;
    assert!(python_result.is_ok());
    assert!(python_result.unwrap().contains("Python"));
}

#[tokio::test]
async fn test_compilation_error_handling() {
    let _ctx = IntegrationTestContext::new();
    let config = Config::load().unwrap();
    let mut runner = DockerRunner::new(config, "rust".to_string()).unwrap();

    let invalid_code = r#"
        fn main() {
            let x: i32 = "not a number";  // Type error
        }
    "#;

    let result = runner.run_in_docker(invalid_code).await;
    assert!(result.is_err());
    let error = result.unwrap_err();
    assert!(error.to_string().contains("error"));
} 