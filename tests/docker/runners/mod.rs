use tokio::test;
use bollard::Docker;
use cph::docker::{DockerRunner, RunnerState, DockerConfig};

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
    
    assert_eq!(runners.get_state().await, RunnerState::Error);
}

#[tokio::test]
async fn test_runners_connection() {
    let docker = Docker::connect_with_local_defaults().unwrap();
    let config = DockerConfig::default();
    let runners = DockerRunners::new(docker, config);
    
    let from = runners.add_runner("python".to_string()).await;
    let to = runners.add_runner("rust".to_string()).await;
    
    runners.connect(from, to).await;
    // 接続の検証は別のテストで行う
} 