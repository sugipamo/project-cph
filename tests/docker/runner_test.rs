use std::process::Command;
use tokio::test;
use cph::docker::config::DockerConfig;
use cph::docker::DockerRunner;
use cph::config::languages::LanguageConfig;

fn load_docker_config() -> DockerConfig {
    DockerConfig::default()
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
    let config = DockerConfig::default();
    let language_info = LanguageConfig::from_yaml("src/config/languages.yaml", "rust").unwrap();
    
    let runner = DockerRunner::new(config, language_info);
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
    
    let config = DockerConfig::default();
    let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "rust").unwrap();
    let mut runner = DockerRunner::new(config, language_config);

    // コンパイル前のディレクトリ構造を確認
    println!("=== Directory Structure Before Compilation ===");
    match runner.inspect_mount_point().await {
        Ok(output) => println!("{}", output),
        Err(e) => println!("Error inspecting directory: {}", e),
    }
    println!("=== End of Directory Structure ===\n");
    
    // Hello Worldプログラム
    let source_code = r#"
        fn main() {
            println!("Hello, World!");
        }
    "#;
    
    // 実行
    let result = runner.run_in_docker(source_code).await;
    
    // コンパイル後のディレクトリ構造を確認
    println!("\n=== Directory Structure After Compilation ===");
    match runner.inspect_mount_point().await {
        Ok(output) => println!("{}", output),
        Err(e) => println!("Error inspecting directory: {}", e),
    }
    println!("=== End of Directory Structure ===");

    assert!(result.is_ok(), "実行に失敗: {:?}", result.err());
    println!("実行結果:\n{}", result.unwrap());
    
    super::teardown();
}

#[tokio::test]
async fn test_timeout() {
    super::setup();
    
    let mut config = DockerConfig::default();
    // タイムアウトを短く設定
    config.timeout_seconds = config.timeout_seconds / 2;
    let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "python").unwrap();
    let mut runner = DockerRunner::new(config, language_config);
    
    // 無限ループのプログラム
    let source_code = "while True: pass";
    
    // 実行
    let result = runner.run_in_docker(source_code).await;
    assert!(result.is_err(), "タイムアウトが発生すべき");
    assert!(result.unwrap_err().contains("timeout"));
    
    super::teardown();
}

#[tokio::test]
async fn test_memory_limit() {
    super::setup();
    
    let mut config = DockerConfig::default();
    // メモリ制限を32MBに設定
    config.memory_limit_mb = 32;
    let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "python").unwrap();
    let mut runner = DockerRunner::new(config, language_config);
    
    // メモリを大量に消費するプログラム
    let source_code = "x = []\nwhile True:\n    x.extend([1] * 1000000)";
    
    // 実行
    let result = runner.run_in_docker(source_code).await;
    assert!(result.is_err(), "メモリ制限エラーが発生すべき");
    assert!(result.unwrap_err().contains("OOM"));
    
    super::teardown();
}

#[tokio::test]
async fn test_compilation_error() {
    super::setup();
    
    let config = DockerConfig::default();
    let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "rust").unwrap();
    let mut runner = DockerRunner::new(config, language_config);
    
    // コンパイルエラーを含むプログラム
    let source_code = r#"
        fn main() {
            let x: i32 = "not a number";  // 型エラー
        }
    "#;
    
    // 実行
    let result = runner.run_in_docker(source_code).await;
    assert!(result.is_err(), "コンパイルエラーが発生すべき");
    
    super::teardown();
}

#[tokio::test]
async fn test_pypy_runner() {
    super::setup();
    
    let config = DockerConfig::default();
    let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "pypy").unwrap();
    let mut runner = DockerRunner::new(config, language_config);
    
    // Hello Worldプログラム
    let source_code = r#"print("Hello, World!")"#;
    
    // 実行
    let result = runner.run_in_docker(source_code).await;
    assert!(result.is_ok(), "実行に失敗: {:?}", result.err());
    assert_eq!(result.unwrap().trim(), "Hello, World!");
    
    super::teardown();
}

#[tokio::test]
async fn test_cpp_runner() {
    super::setup();
    
    let config = DockerConfig::default();
    let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "cpp").unwrap();
    let mut runner = DockerRunner::new(config, language_config);
    
    // Hello Worldプログラム
    let source_code = r#"
        #include <iostream>
        int main() {
            std::cout << "Hello, World!" << std::endl;
            return 0;
        }
    "#;
    
    // 実行
    let result = runner.run_in_docker(source_code).await;
    assert!(result.is_ok(), "実行に失敗: {:?}", result.err());
    assert_eq!(result.unwrap().trim(), "Hello, World!");
    
    super::teardown();
} 