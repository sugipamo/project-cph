use std::process::Command;
use tokio::runtime::Runtime;
use cph::docker::DockerRunner;
use cph::docker::config::{RunnerConfig, LanguageConfig, DockerConfig};
use serde::Deserialize;

fn load_docker_config() -> DockerConfig {
    DockerConfig::from_yaml("src/config/docker.yaml").unwrap()
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
        // docker.yamlから設定を読み込む
        let config = RunnerConfig::from_yaml("src/config/docker.yaml").unwrap();
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
        // docker.yamlから設定を読み込む
        let config = RunnerConfig::from_yaml("src/config/docker.yaml").unwrap();
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
        // docker.yamlから設定を読み込む
        let mut config = RunnerConfig::from_yaml("src/config/docker.yaml").unwrap();
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
    });
    super::teardown();
}

#[test]
fn test_memory_limit() {
    super::setup();
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        // docker.yamlから設定を読み込む
        let mut config = RunnerConfig::from_yaml("src/config/docker.yaml").unwrap();
        // メモリ制限を6MBに設定
        config.memory_limit_mb = 6;
        let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "python").unwrap();
        let mut runner = DockerRunner::new(config, language_config);
        
        // メモリを大量に消費するプログラム
        let source_code = r#"
            x = []
            while True:
                x.extend([1] * 1000000)
        "#;
        
        // 実行
        let result = runner.run_in_docker(source_code).await;
        assert!(result.is_err(), "メモリ制限エラーが発生すべき");
        assert!(result.unwrap_err().contains("OOM"));
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
        let config = RunnerConfig::new(
            docker_config.timeout_seconds,
            docker_config.memory_limit_mb,
            docker_config.mount_point
        );
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

#[test]
fn test_pypy_runner() {
    super::setup();
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        // docker.yamlから設定を読み込む
        let config = RunnerConfig::from_yaml("src/config/docker.yaml").unwrap();
        let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "pypy").unwrap();
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
fn test_cpp_runner() {
    super::setup();
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        // docker.yamlから設定を読み込む
        let config = RunnerConfig::from_yaml("src/config/docker.yaml").unwrap();
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
    });
    super::teardown();
} 