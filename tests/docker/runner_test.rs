use std::process::Command;
use tokio::runtime::Runtime;
use cph::docker::DockerRunner;
use cph::docker::{RunnerConfig, LanguageConfig};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct DockerConfig {
    timeout_seconds: u64,
    memory_limit_mb: u64,
}

fn load_docker_config() -> DockerConfig {
    let content = std::fs::read_to_string("src/config/docker.yaml").unwrap();
    serde_yaml::from_str(&content).unwrap()
}

// Dockerデーモンが利用可能かチェックする
fn check_docker_available() -> bool {
    Command::new("docker")
        .arg("info")
        .output()
        .map(|output| output.status.success())
        .unwrap_or(false)
}

#[test]
fn test_docker_available() {
    assert!(check_docker_available(), "Dockerが利用できません");
}

#[test]
fn test_python_runner() {
    super::setup();
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        // Pythonランナーの作成
        let mut runner = DockerRunner::from_language("python").unwrap();
        
        // Hello Worldプログラム
        let source_code = r#"print("Hello, World!")"#;
        
        // 実行
        let result = runner.run_in_docker(source_code).await;
        assert!(result.is_ok(), "実行に失敗: {:?}", result.err());
        assert_eq!(result.unwrap().trim(), "Hello, World!");
    });
    super::teardown();
}

#[test]
fn test_rust_runner() {
    super::setup();
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        // Rustランナーの作成
        let mut runner = DockerRunner::from_language("rust").unwrap();
        
        // Hello Worldプログラム
        let source_code = r#"
            fn main() {
                println!("Hello, World!");
            }
        "#;
        
        // 実行
        let result = runner.run_in_docker(source_code).await;
        assert!(result.is_ok(), "実行に失敗: {:?}", result.err());
        assert_eq!(result.unwrap().trim(), "Hello, World!");
    });
    super::teardown();
}

#[test]
fn test_timeout() {
    super::setup();
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        let docker_config = load_docker_config();
        // 設定されたタイムアウトの半分の時間を使用
        let timeout = docker_config.timeout_seconds / 2;
        let config = RunnerConfig::new(timeout, docker_config.memory_limit_mb);
        let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "python").unwrap();
        let mut runner = DockerRunner::new(config, language_config);
        
        // 無限ループのプログラム
        let source_code = "while True: pass";
        
        // 実行
        let result = runner.run_in_docker(source_code).await;
        assert!(result.is_err(), "タイムアウトが発生すべき");
        assert!(result.unwrap_err().contains("timeout"));
    });
    super::teardown();
}

#[test]
fn test_memory_limit() {
    super::setup();
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        let docker_config = load_docker_config();
        // メモリ制限を10MBに設定
        let config = RunnerConfig::new(docker_config.timeout_seconds, 10);
        let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "python").unwrap();
        let mut runner = DockerRunner::new(config, language_config);
        
        // メモリを大量に消費するプログラム
        let source_code = "x = [0] * 1000000000";
        
        // 実行
        let result = runner.run_in_docker(source_code).await;
        assert!(result.is_err(), "メモリ制限エラーが発生すべき");
    });
    super::teardown();
}

#[test]
fn test_compilation_error() {
    super::setup();
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        // Rustランナーの作成
        let mut runner = DockerRunner::from_language("rust").unwrap();
        
        // コンパイルエラーを含むプログラム
        let source_code = r#"
            fn main() {
                let x: i32 = "not a number";  // 型エラー
            }
        "#;
        
        // 実行
        let result = runner.run_in_docker(source_code).await;
        assert!(result.is_err(), "コンパイルエラーが発生すべき");
    });
    super::teardown();
} 