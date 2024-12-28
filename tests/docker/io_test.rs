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
    let config_path = PathBuf::from("src/config/runner.yaml");
    let config = RunnerConfig::load(&config_path).unwrap();
    println!("Config loaded");

    // DockerRunnerの初期化
    let mut runner = DockerRunner::new(docker, config, "python".to_string());
    println!("DockerRunner created");

    // Pythonのソースコード（よンプルな実装）
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
        println!("Current buffer contents before wait: {:?}", all_output);

        // 出力を待つ時間を延長し、複数回チェック
        for _ in 0..5 {
            sleep(Duration::from_millis(100)).await;
            let current_output = runner.read_all().await.unwrap();
            println!("Buffer contents during wait: {:?}", current_output);
            if !current_output.is_empty() {
                break;
            }
        }

        let output = runner.read().await.unwrap();
        println!("Final received output: {}", output);

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