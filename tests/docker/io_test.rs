use bollard::Docker;
use std::path::PathBuf;
use cph::docker::{DockerRunner, RunnerConfig, RunnerState};
use tokio::time::sleep;
use std::time::Duration;

#[tokio::test]
async fn test_python_io() {
    // Dockerクライアントの初期化
    let docker = Docker::connect_with_local_defaults().unwrap();
    println!("Docker client initialized");
    
    // 設定の読み込み
    let config_path = PathBuf::from("config/runner.yaml");
    let config = RunnerConfig::load(&config_path).unwrap();
    println!("Config loaded");

    // DockerRunnerの初期化
    let mut runner = DockerRunner::new(docker, config, "python".to_string());
    println!("DockerRunner created");

    // Pythonのソースコード（より単純な実装）
    let source_code = "while True: print(int(input()) + 1)";
    println!("Source code: {}", source_code);

    // コードの実行
    let output = runner.run_in_docker(source_code).await.unwrap();
    println!("Initial container output: stdout={:?}, stderr={:?}", output.stdout, output.stderr);

    // コンテナの状態を確認
    let state = runner.get_state().await;
    println!("Container state: {:?}", state);
    assert_eq!(state, RunnerState::Running);

    // 入力データの送信と出力の確認
    for i in 1..=2 {
        println!("\nTest iteration {}", i);
        println!("Sending input: {}", i);
        runner.write(&format!("{}\n", i)).await.unwrap();

        // バッファの現在の状態を確認
        let all_output = runner.read_all().await.unwrap();
        println!("Current buffer contents: {:?}", all_output);

        // 出力を待つ
        sleep(Duration::from_millis(50)).await;
        let output = runner.read().await.unwrap();
        println!("Received output: {}", output);
        
        // エラー出力も確認
        let error = runner.read_error().await.unwrap();
        if !error.is_empty() {
            println!("Error output: {}", error);
        }

        assert_eq!(output.trim(), &(i + 1).to_string(), "Expected {}, got {}", i + 1, output.trim());
    }

    // 実行の終了
    println!("\nStopping container");
    runner.stop().await.unwrap();
    println!("Container stopped");
} 