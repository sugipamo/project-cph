use std::process::Command;
use tokio::runtime::Runtime;
use cph::docker::DockerRunner;
use cph::docker::{RunnerConfig, LanguageConfig};

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
        // 短いタイムアウトで設定
        let config = RunnerConfig::new(1, 512);  // 1秒タイムアウト
        let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "python").unwrap();
        let mut runner = DockerRunner::new(config, language_config);
        
        // 無限ループのプログラム
        let source_code = "while True: pass";  // インデントを削除
        
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
        // 小さいメモリ制限で設定
        let config = RunnerConfig::new(5, 10);  // 10MB制限
        let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "python").unwrap();
        let mut runner = DockerRunner::new(config, language_config);
        
        // メモリを大量に消費するプログラム
        let source_code = "x = [0] * 1000000000";  // インデントを削除
        
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