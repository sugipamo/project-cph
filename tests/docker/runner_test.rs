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
        let docker_config = load_docker_config();
        // Pythonランナーの作成（設定ファイルから値を読み込む）
        let config = RunnerConfig::new(docker_config.timeout_seconds, docker_config.memory_limit_mb);
        let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "python").unwrap();
        let mut runner = DockerRunner::new(config, language_config);
        
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
        let docker_config = load_docker_config();
        // Rustランナーの作成（設定ファイルから値を読み込む）
        let config = RunnerConfig::new(docker_config.timeout_seconds, docker_config.memory_limit_mb);
        let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "rust").unwrap();
        let mut runner = DockerRunner::new(config, language_config);
        
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
        // メモリ制限を6MBに設定（Dockerの最小制限）
        let config = RunnerConfig::new(docker_config.timeout_seconds, 6);
        let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "python").unwrap();
        let mut runner = DockerRunner::new(config, language_config);
        
        // メモリを大量に消費するプログラム（より確実なメモリ確保）
        let source_code = r#"
# メモリを大量に消費するプログラム
memory = []
try:
    # 一度に大きなメモリを確保して確実にOOMを発生させる
    chunk = bytearray(20 * 1024 * 1024)  # 20MB（制限の約3倍）
    memory.append(chunk)
    print("Memory allocation succeeded unexpectedly")
except MemoryError:
    print("Memory allocation failed")
    exit(137)  # OOMエラーを示す終了コード
"#;
        
        // 実行
        let result = runner.run_in_docker(source_code).await;
        assert!(result.is_err(), "メモリ制限エラーが発生すべき");
        let err = result.unwrap_err();
        assert!(err.contains("exit code") || err.contains("killed") || err.contains("OOM") || err.contains("137"),
                "期待されるエラーメッセージが含まれていません: {}", err);
    });
    super::teardown();
}

#[test]
fn test_compilation_error() {
    super::setup();
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        let docker_config = load_docker_config();
        // Rustランナーの作成（設定ファイルから値を読み込む）
        let config = RunnerConfig::new(docker_config.timeout_seconds, docker_config.memory_limit_mb);
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
    });
    super::teardown();
} 