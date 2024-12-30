use bollard::Docker;
use std::time::Duration;
use cph::docker::{DockerRunner, RunnerState, RunnerConfig};

#[tokio::test]
async fn test_basic_pipeline() {
    let docker = Docker::connect_with_local_defaults().expect("Failed to connect to Docker");
    let config = RunnerConfig::default();
    let mut runner = DockerRunner::new(docker, config, "python".to_string());

    runner.run_in_docker("print('Hello, World!')").await;
    assert_eq!(runner.get_state().await, RunnerState::Running);

    let output = runner.read().await;
    assert_eq!(output.trim(), "Hello, World!");

    runner.stop().await;
    assert_eq!(runner.get_state().await, RunnerState::Stop);
}

#[tokio::test]
async fn test_error_handling() {
    let docker = Docker::connect_with_local_defaults().expect("Failed to connect to Docker");
    let config = RunnerConfig::default();

    // コンパイルエラーのテスト
    let mut runner = DockerRunner::new(docker.clone(), config.clone(), "python".to_string());
    runner.run_in_docker("invalid python code").await;
    assert_eq!(runner.get_state().await, RunnerState::Error);

    // 未サポート言語のテスト
    let mut runner = DockerRunner::new(docker, config, "unsupported_language".to_string());
    runner.run_in_docker("code").await;
    assert_eq!(runner.get_state().await, RunnerState::Error);
}

#[tokio::test]
async fn test_timeout_handling() {
    let docker = Docker::connect_with_local_defaults().expect("Failed to connect to Docker");
    let mut config = RunnerConfig::default();
    config.timeout_seconds = 1;
    let mut runner = DockerRunner::new(docker, config, "python".to_string());

    runner.run_in_docker("while True: pass").await;
    tokio::time::sleep(Duration::from_secs(2)).await;
    assert_eq!(runner.get_state().await, RunnerState::Error);
}

#[tokio::test]
async fn test_concurrent_runners() {
    let docker = Docker::connect_with_local_defaults().expect("Failed to connect to Docker");
    let config = RunnerConfig::default();

    let mut runners = vec![];
    for i in 0..3 {
        let mut runner = DockerRunner::new(docker.clone(), config.clone(), "python".to_string());
        runner.run_in_docker(&format!("print('Runner {}')", i)).await;
        runners.push(runner);
    }

    for (i, mut runner) in runners.into_iter().enumerate() {
        let output = runner.read().await;
        assert_eq!(output.trim(), format!("Runner {}", i));
        runner.stop().await;
        assert_eq!(runner.get_state().await, RunnerState::Stop);
    }
} 