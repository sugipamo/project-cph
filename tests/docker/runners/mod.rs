use tokio::test;
use bollard::Docker;
use tokio::time::{sleep, Duration};
use cph::docker::{DockerRunner, RunnerState, DockerConfig, DockerRunners};

#[tokio::test]
async fn test_runners_creation() {
    let docker = Docker::connect_with_local_defaults().unwrap();
    let config = DockerConfig::default();
    let runners = DockerRunners::new(docker, config);
    assert_eq!(runners.get_state().await, RunnerState::Ready);
}

#[tokio::test]
async fn test_runners_add() {
    let docker = Docker::connect_with_local_defaults().unwrap();
    let config = DockerConfig::default();
    let runners = DockerRunners::new(docker, config);
    
    let id = runners.add_runner("python".to_string()).await;
    assert_eq!(id, 0);
    
    let id = runners.add_runner("rust".to_string()).await;
    assert_eq!(id, 1);
}

#[tokio::test]
async fn test_runners_timeout() {
    let docker = Docker::connect_with_local_defaults().unwrap();
    let mut config = DockerConfig::default();
    config.timeout_seconds = 1;  // タイムアウトを1秒に設定
    let runners = DockerRunners::new(docker, config);
    
    let id = runners.add_runner("python".to_string()).await;
    runners.run_code(id, "while True: pass").await;
    
    // タイムアウトの発生を待つ
    sleep(Duration::from_secs(2)).await;
    
    // 状態を確認
    let state = runners.get_state().await;
    assert_eq!(state, RunnerState::Error, "タイムアウトエラーが発生すべき");
}

#[tokio::test]
async fn test_runners_connection() {
    let docker = Docker::connect_with_local_defaults().unwrap();
    let config = DockerConfig::default();
    let runners = DockerRunners::new(docker, config);
    
    // Pythonランナーを作成（出力を生成）
    let from = runners.add_runner("python".to_string()).await;
    runners.run_code(from, r#"print("Test message")"#).await;
    
    // Rustランナーを作成（出力を受信）
    let to = runners.add_runner("rust".to_string()).await;
    runners.connect(from, to).await;
    
    // 接続を検証
    sleep(Duration::from_millis(500)).await;  // 出力の伝播を待つ
    
    let output = runners.get_output(to).await;
    assert!(output.contains("Test message"), "接続されたランナーが出力を受信すべき");
} 