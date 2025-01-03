use std::process::Command;
use tokio::test;
use cph::config::Config;
use cph::docker::DockerRunner;

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

    // コンパイル前のディレクトリ構造を確認
    println!("=== Directory Structure Before Compilation ===");
    match runner.inspect_mount_point().await {
        Ok(output) => println!("{}", output),
        Err(e) => println!("Error: {}", e),
    }

    let source_code = r#"
        fn main() {
            println!("Hello from Rust!");
        }
    "#;

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
        Err(e) => assert!(e.contains("timeout")),
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
        Ok(_) => panic!("メモリ制限が機能していません"),
        Err(e) => assert!(e.contains("memory") || e.contains("killed")),
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
        Err(e) => assert!(e.contains("error")),
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
        Ok(output) => assert!(output.contains("Hello from PyPy!")),
        Err(e) => panic!("PyPyの実行に失敗しました: {}", e),
    }
}

#[tokio::test]
async fn test_cpp_runner() {
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
        Ok(output) => assert!(output.contains("Hello from C++!")),
        Err(e) => panic!("C++の実行に失敗しました: {}", e),
    }
} 