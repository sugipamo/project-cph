use std::process::Command;
use cph::config::Config;
use cph::docker::{DockerRunner, DockerError};
use std::fs;
use std::path::PathBuf;
use std::os::unix::fs::PermissionsExt;
use crate::helpers::docker_debug;

fn setup() -> PathBuf {
    let temp_dir = std::env::temp_dir().join("cph-test");
    fs::create_dir_all(&temp_dir).unwrap();
    temp_dir
}

fn teardown(temp_dir: &PathBuf) {
    let _ = fs::remove_dir_all(temp_dir);
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
    let temp_dir = setup();
    println!("=== Test Directory ===");
    println!("{}", temp_dir.display());
    
    let config = Config::load().unwrap();
    let mut runner = DockerRunner::new(config, "rust".to_string()).unwrap();

    let source_code = r#"fn main() {
    println!("Hello from Rust!");
}"#;

    println!("=== Initial Directory State ===");
    println!("{}", docker_debug::inspect_directory(&temp_dir));

    match runner.run_in_docker(source_code).await {
        Ok(output) => {
            println!("=== Execution Output ===");
            println!("{}", output);
            println!("=== Final Directory State ===");
            println!("{}", docker_debug::inspect_directory(&temp_dir));
            assert!(output.contains("Hello from Rust!"));
        }
        Err(e) => {
            println!("Error: {}", e);
            println!("=== Final Directory State ===");
            println!("{}", docker_debug::inspect_directory(&temp_dir));
            panic!("実行に失敗しました");
        }
    }

    teardown(&temp_dir);
}

#[tokio::test]
async fn test_timeout() {
    let temp_dir = setup();
    
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

    teardown(&temp_dir);
}

#[tokio::test]
async fn test_memory_limit() {
    let temp_dir = setup();
    
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

    teardown(&temp_dir);
}

#[tokio::test]
async fn test_compilation_error() {
    let temp_dir = setup();
    
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

    teardown(&temp_dir);
}

#[tokio::test]
async fn test_pypy_runner() {
    let temp_dir = setup();
    
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

    teardown(&temp_dir);
}

#[tokio::test]
async fn test_python_runner() {
    let temp_dir = setup();
    
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

    teardown(&temp_dir);
}

#[tokio::test]
async fn test_cpp_runner_with_extension() {
    let temp_dir = setup();
    
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

    teardown(&temp_dir);
}

#[tokio::test]
async fn test_rust_runner_with_extension() {
    let temp_dir = setup();
    
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

    teardown(&temp_dir);
}

#[tokio::test]
async fn test_mount_point() {
    let temp_dir = setup();
    
    let config = Config::load().unwrap();
    let mut runner = DockerRunner::new(config, "rust".to_string()).unwrap();

    // テスト用のファイルを作成
    let test_file = temp_dir.join("test.txt");
    fs::write(&test_file, "test content").unwrap();
    fs::set_permissions(&test_file, fs::Permissions::from_mode(0o644)).unwrap();

    println!("=== Local Directory Contents ===");
    println!("{}", docker_debug::inspect_directory(&temp_dir));

    // 単純なファイル読み込みプログラムを実行
    let source_code = r#"
        use std::fs;
        fn main() {
            match fs::read_to_string("/app/test.txt") {
                Ok(content) => println!("File content: {}", content),
                Err(e) => eprintln!("Error reading file: {}", e),
            }
        }
    "#;

    match runner.run_in_docker(source_code).await {
        Ok(output) => {
            println!("=== Execution Output ===");
            println!("{}", output);
            assert!(output.contains("test content"), "ファイルの内容が読み取れません\n出力: {}", output);
        }
        Err(e) => {
            println!("=== Error Output ===");
            println!("Error: {}", e);
            panic!("マウントポイントのテストに失敗しました: {}", e);
        }
    }

    teardown(&temp_dir);
} 