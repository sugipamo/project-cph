use std::time::Duration;
use tokio::time::sleep;
use bollard::Docker;

use cph::docker::{DockerRunner, RunnerState, RunnerConfig, DockerError};

#[tokio::test]
async fn test_basic_pipeline() -> std::result::Result<(), Box<dyn std::error::Error>> {
    let config = RunnerConfig::load("src/config/docker.yaml")?;
    let docker = Docker::connect_with_local_defaults().map_err(DockerError::ConnectionError)?;
    let mut runner = DockerRunner::new(docker.clone(), config.clone(), "python".to_string());

    // 初期化
    runner.initialize("print('hello')").await?;
    assert_eq!(runner.get_state().await, RunnerState::Running);

    // 出力の確認
    let output = runner.read().await?;
    assert_eq!(output.trim(), "hello");

    // 入力の送信
    runner.write("test\n").await?;

    // 停止処理
    runner.stop().await?;
    assert_eq!(runner.get_state().await, RunnerState::Stop);

    Ok(())
}

#[tokio::test]
async fn test_error_handling() -> std::result::Result<(), Box<dyn std::error::Error>> {
    let config = RunnerConfig::load("src/config/docker.yaml")?;
    let docker = Docker::connect_with_local_defaults().map_err(DockerError::ConnectionError)?;
    let mut runner = DockerRunner::new(docker.clone(), config.clone(), "python".to_string());

    // 構文エラーのあるコードで初期化
    let result = runner.initialize("print('hello'").await;
    assert!(matches!(result, Err(DockerError::CompilationError(_))));

    // 存在しない言語での初期化
    let mut invalid_runner = DockerRunner::new(docker.clone(), config.clone(), "invalid_lang".to_string());
    let result = invalid_runner.initialize("print('hello')").await;
    assert!(matches!(result, Err(DockerError::UnsupportedLanguage(_))));

    Ok(())
}

#[tokio::test]
async fn test_timeout_handling() -> std::result::Result<(), Box<dyn std::error::Error>> {
    let config = RunnerConfig::load("src/config/docker.yaml")?;
    let docker = Docker::connect_with_local_defaults().map_err(DockerError::ConnectionError)?;
    let mut runner = DockerRunner::new(docker.clone(), config.clone(), "python".to_string());

    // 無限ループのコードで初期化
    runner.initialize("while True: pass").await?;
    
    // タイムアウトの確認
    let result = runner.wait_for_stop(Duration::from_secs(2)).await;
    assert!(matches!(result, Err(DockerError::Timeout)));
    
    // 強制停止の確認
    runner.force_stop().await?;
    assert_eq!(runner.get_state().await, RunnerState::Stop);

    Ok(())
}

#[tokio::test]
async fn test_concurrent_runners() -> std::result::Result<(), Box<dyn std::error::Error>> {
    let config = RunnerConfig::load("src/config/docker.yaml")?;
    let docker = Docker::connect_with_local_defaults().map_err(DockerError::ConnectionError)?;
    let mut runner1 = DockerRunner::new(docker.clone(), config.clone(), "python".to_string());
    let mut runner2 = DockerRunner::new(docker.clone(), config.clone(), "python".to_string());

    // 両方のランナーを初期化
    runner1.initialize("print('runner1')").await?;
    runner2.initialize("print('runner2')").await?;

    // 両方のランナーが実行中であることを確認
    assert_eq!(runner1.get_state().await, RunnerState::Running);
    assert_eq!(runner2.get_state().await, RunnerState::Running);

    // 出力の確認
    let output1 = runner1.read().await?;
    let output2 = runner2.read().await?;
    assert_eq!(output1.trim(), "runner1");
    assert_eq!(output2.trim(), "runner2");

    // 両方のランナーを停止
    runner1.stop().await?;
    runner2.stop().await?;

    // 両方のランナーが停止していることを確認
    assert_eq!(runner1.get_state().await, RunnerState::Stop);
    assert_eq!(runner2.get_state().await, RunnerState::Stop);

    Ok(())
} 