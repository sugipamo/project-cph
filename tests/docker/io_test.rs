use tokio::test;
use std::path::PathBuf;
use cph::docker::{DockerRunner, DockerConfig};
use cph::config::languages::LanguageConfig;

#[tokio::test]
async fn test_io_operations() {
    super::setup();

    let config_path = PathBuf::from("src/config/docker.yaml");
    let config = DockerConfig::from_yaml(&config_path).unwrap_or_else(|e| {
        println!("Failed to load config: {}", e);
        DockerConfig::default()
    });

    let language_config = LanguageConfig::from_yaml("src/config/languages.yaml", "python").unwrap();
    let mut runner = DockerRunner::new(config, language_config);

    // 入出力のテスト用プログラム
    let source_code = r#"
import sys

# 標準入力から読み込み
input_line = sys.stdin.readline().strip()
print(f"Received: {input_line}")

# 標準エラー出力にも出力
sys.stderr.write("Error message test\n")
sys.stderr.flush()
"#;

    // プログラムの実行
    let result = runner.run_in_docker(source_code).await;
    assert!(result.is_ok(), "実行に失敗: {:?}", result.err());

    // 入力の送信
    runner.write("Hello from test\n").await
        .expect("入力の送信に失敗");

    // 出力の確認
    let output = runner.read().await
        .expect("出力の読み取りに失敗");
    assert!(output.contains("Received: Hello from test"), 
        "期待する出力が含まれていません: {}", output);

    // エラー出力の確認
    let error = runner.read_error().await
        .expect("エラー出力の読み取りに失敗");
    assert!(error.contains("Error message test"), 
        "期待するエラーメッセージが含まれていません: {}", error);

    super::teardown();
} 