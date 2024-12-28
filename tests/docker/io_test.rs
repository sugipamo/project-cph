use bollard::Docker;
use std::path::PathBuf;
use cph::docker::{DockerRunner, RunnerConfig, RunnerState};
use tokio::time::sleep;
use std::time::Duration;

#[derive(Default)]
struct TestState {
    all_outputs: Vec<String>,
    buffer_states: Vec<Vec<String>>,
    error_outputs: Vec<String>,
    last_input: Option<String>,
}

#[tokio::test]
async fn test_python_io() {
    let mut state = TestState::default();
    
    // Dockerクライアントの初期化
    let docker = Docker::connect_with_local_defaults().unwrap_or_else(|e| {
        println!("Docker initialization failed: {:?}", e);
        panic!("Docker client initialization failed");
    });

    // 設定の読み込み
    let config_path = PathBuf::from("src/config/runner.yaml");
    let config = RunnerConfig::load(&config_path).unwrap_or_else(|e| {
        println!("Config loading failed: {:?}", e);
        panic!("Failed to load config");
    });

    // DockerRunnerの初期化
    let mut runner = DockerRunner::new(docker, config, "python".to_string());
    
    // Pythonのソースコード
    let source_code = "while True: print(int(input()) + 1)";
    
    // コードの実行
    let output = runner.run_in_docker(source_code).await.unwrap_or_else(|e| {
        println!("Source code: {}", source_code);
        println!("Failed to run code in docker: {:?}", e);
        panic!("Docker execution failed");
    });
    
    if !output.stdout.is_empty() || !output.stderr.is_empty() {
        println!("Initial container output: stdout={:?}, stderr={:?}", output.stdout, output.stderr);
    }

    // コンテナの状態を確認
    let state_check = runner.get_state().await;
    assert_eq!(state_check, RunnerState::Running, "Container is not in running state");

    // 入力データの送信と出力の確認
    for i in 1..=2 {
        state.last_input = Some(format!("{}\n", i));
        
        // 入力を送信
        if let Err(e) = runner.write(&state.last_input.as_ref().unwrap()).await {
            println!("Test iteration {}", i);
            println!("Failed to write input: {:?}", e);
            print_debug_info(&state);
            panic!("Failed to write to container");
        }

        // バッファの状態を確認と保存
        let mut success = false;
        for attempt in 0..5 {
            sleep(Duration::from_millis(100)).await;
            let current_output = runner.read_all().await.unwrap_or_else(|e| {
                println!("Failed to read output on attempt {}: {:?}", attempt, e);
                print_debug_info(&state);
                panic!("Failed to read from container");
            });
            
            state.buffer_states.push(current_output.clone());
            
            if !current_output.is_empty() {
                success = true;
                break;
            }
        }

        if !success {
            println!("Test iteration {}", i);
            println!("Failed to receive output after all attempts");
            print_debug_info(&state);
            panic!("No output received from container");
        }

        // 出力の確認
        let output = runner.read().await.unwrap_or_else(|e| {
            println!("Failed to read final output: {:?}", e);
            print_debug_info(&state);
            panic!("Failed to read final output");
        });
        state.all_outputs.push(output.clone());

        // エラー出力の確認と保存
        let error = runner.read_error().await.unwrap_or_else(|e| {
            println!("Failed to read error output: {:?}", e);
            print_debug_info(&state);
            panic!("Failed to read error output");
        });
        if !error.is_empty() {
            state.error_outputs.push(error.clone());
        }

        assert_eq!(
            output.trim(), 
            &(i + 1).to_string(),
            "Expected {}, got {} (printing debug info)",
            i + 1,
            output.trim()
        );
    }

    // 実行の終了
    if let Err(e) = runner.stop().await {
        println!("Failed to stop container: {:?}", e);
        print_debug_info(&state);
        panic!("Failed to stop container");
    }
}

fn print_debug_info(state: &TestState) {
    println!("\n=== Debug Information ===");
    println!("Last Input: {:?}", state.last_input);
    println!("All Outputs: {:?}", state.all_outputs);
    println!("Buffer States History: {:?}", state.buffer_states);
    println!("Error Outputs: {:?}", state.error_outputs);
    println!("========================\n");
} 