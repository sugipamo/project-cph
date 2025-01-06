use std::process::Command;
use tokio::test;
use cph::config::Config;
use cph::docker::{DockerRunner, DockerError};
use std::fs;

// Dockerデーモンが利用可能かチェックする
fn check_docker_available() -> bool {
    Command::new("docker")
        .arg("info")
        .output()
        .map(|output| output.status.success())
        .unwrap_or(false)
}

#[tokio::test]
async fn test_docker_runner_creation() {
    let config = Config::load().unwrap();
    let runner = DockerRunner::new(config, "rust".to_string()).unwrap();
    assert!(runner.get_state().await == cph::docker::RunnerState::Ready);
}

#[tokio::test]
async fn test_docker_runner_from_language() {
    let runner = DockerRunner::from_language("rust").unwrap();
    assert!(runner.get_state().await == cph::docker::RunnerState::Ready);
}

#[tokio::test]
async fn test_docker_available() {
    assert!(check_docker_available(), "Dockerが利用できません");
}

#[tokio::test]
async fn test_rust_runner() {
    super::setup();
    
    let config = Config::load().unwrap();
    let mut runner = DockerRunner::new(config, "rust".to_string()).unwrap();

    let source_code = r#"fn main() {
    println!("Hello from Rust!");
}"#;

    match runner.run_in_docker(source_code).await {
        Ok(output) => {
            println!("=== Execution Output ===");
            println!("{}", output);
            assert!(output.contains("Hello from Rust!"));
        }
        Err(e) => {
            println!("Error: {}", e);
            panic!("実行に失敗しました");
        }
    }
}

#[tokio::test]
async fn test_timeout() {
    super::setup();
    
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
    super::setup();
    
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
        Ok(_) => panic!("メモリ制限が機能してせんでした"),
        Err(e) => match e {
            DockerError::Memory(_) | DockerError::Runtime(_) => (),
            _ => panic!("予期しないエラー: {}", e),
        },
    }
}

#[tokio::test]
async fn test_compilation_error() {
    super::setup();
    
    let config = Config::load().unwrap();
    let mut runner = DockerRunner::new(config, "rust".to_string()).unwrap();

    let source_code = r#"
        fn main() {
            let x: i32 = "not a number";
        }
    "#;

    match runner.run_in_docker(source_code).await {
        Ok(_) => panic!("コンパイルエラーが検出されませんでした"),
        Err(e) => assert!(e.to_string().contains("error")),
    }
}

#[tokio::test]
async fn test_pypy_runner() {
    super::setup();
    
    let config = Config::load().unwrap();
    let mut runner = DockerRunner::new(config, "pypy".to_string()).unwrap();

    let source_code = r#"
print("Hello from PyPy!")
    "#;

    match runner.run_in_docker(source_code).await {
        Ok(output) => {
            println!("=== PyPy Execution Output ===");
            println!("{}", output);
            assert!(output.contains("Hello from PyPy!"));
        }
        Err(e) => {
            println!("Error: {}", e);
            panic!("PyPyの実行に失敗しました: {}", e);
        }
    }
}

#[tokio::test]
async fn test_python_runner() {
    super::setup();
    
    let config = Config::load().unwrap();
    let mut runner = DockerRunner::new(config, "python".to_string()).unwrap();

    let source_code = r#"
print("Hello from Python!")
    "#;

    match runner.run_in_docker(source_code).await {
        Ok(output) => {
            println!("=== Python Execution Output ===");
            println!("{}", output);
            assert!(output.contains("Hello from Python!"));
        }
        Err(e) => {
            println!("Error: {}", e);
            panic!("Pythonの実行に失敗しました: {}", e);
        }
    }
}

#[tokio::test]
async fn test_cpp_runner_with_extension() {
    super::setup();
    
    let config = Config::load().unwrap();
    let mut runner = DockerRunner::new(config, "cpp".to_string()).unwrap();

    let source_code = r#"
#include <iostream>
int main() {
    std::cout << "Hello from C++!" << std::endl;
    return 0;
}
    "#;

    match runner.run_in_docker(source_code).await {
        Ok(output) => {
            println!("=== C++ Execution Output ===");
            println!("{}", output);
            assert!(output.contains("Hello from C++!"));
        }
        Err(e) => {
            println!("Error: {}", e);
            panic!("C++の実行に失敗しました: {}", e);
        }
    }
}

#[tokio::test]
async fn test_rust_runner_with_extension() {
    super::setup();
    
    let config = Config::load().unwrap();
    let mut runner = DockerRunner::new(config, "rust".to_string()).unwrap();

    let source_code = r#"fn main() {
    println!("Hello from Rust!");
}"#;

    match runner.run_in_docker(source_code).await {
        Ok(output) => {
            println!("=== Rust Execution Output ===");
            println!("{}", output);
            assert!(output.contains("Hello from Rust!"));
        }
        Err(e) => {
            println!("Error: {}", e);
            panic!("Rustの実行に失敗しました: {}", e);
        }
    }
} 