use super::get_test_config_path;
use cph::docker::runner::DockerRunner;
use tokio::time::sleep;
use std::time::Duration;

#[tokio::test]
async fn test_input_output() {
    let mut runner = DockerRunner::new(get_test_config_path(), "python").await.unwrap();
    
    // 入力を受け付けるプログラム
    runner.initialize(r#"
        name = input()
        age = input()
        print(f'Hello, {name}!')
        print(f'You are {age} years old.')
    "#).await.unwrap();
    
    // 入力を送信
    runner.write("Alice").await.unwrap();
    sleep(Duration::from_millis(100)).await;
    runner.write("20").await.unwrap();
    sleep(Duration::from_millis(100)).await;
    
    // 出力を確認
    let outputs = runner.read_all().await.unwrap();
    assert!(outputs.iter().any(|s| s.contains("Hello, Alice!")));
    assert!(outputs.iter().any(|s| s.contains("You are 20 years old.")));
}

#[tokio::test]
async fn test_error_output() {
    let mut runner = DockerRunner::new(get_test_config_path(), "python").await.unwrap();
    
    // エラーを発生させるプログラム
    runner.initialize(r#"
        raise ValueError('Custom error message')
    "#).await.unwrap();
    
    sleep(Duration::from_millis(100)).await;
    
    // エラー出力を確認
    let errors = runner.read_error_all().await.unwrap();
    assert!(errors.iter().any(|s| s.contains("ValueError")));
    assert!(errors.iter().any(|s| s.contains("Custom error message")));
}

#[tokio::test]
async fn test_timeout() {
    let mut runner = DockerRunner::new(get_test_config_path(), "python").await.unwrap();
    
    // 無限ループのプログラム
    runner.initialize(r#"
        while True:
            pass
    "#).await.unwrap();
    
    // タイムアウトを待つ
    sleep(Duration::from_secs(6)).await;
    
    // 実行状態を確認
    let state = runner.get_state().await.unwrap();
    assert!(matches!(state, cph::docker::state::RunnerState::Error));
}

#[tokio::test]
async fn test_multiple_inputs() {
    let mut runner = DockerRunner::new(get_test_config_path(), "python").await.unwrap();
    
    // 複数の入力を処理するプログラム
    runner.initialize(r#"
        while True:
            try:
                line = input()
                if line == "exit":
                    break
                print(f'Echo: {line}')
            except EOFError:
                break
    "#).await.unwrap();
    
    // 複数の入力を送信
    let inputs = vec!["Hello", "World", "exit"];
    for input in inputs {
        runner.write(input).await.unwrap();
        sleep(Duration::from_millis(100)).await;
    }
    
    // 出力を確認
    let outputs = runner.read_all().await.unwrap();
    assert!(outputs.iter().any(|s| s.contains("Echo: Hello")));
    assert!(outputs.iter().any(|s| s.contains("Echo: World")));
} 