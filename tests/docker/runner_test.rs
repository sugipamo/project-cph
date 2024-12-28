use super::get_test_config_path;
use cph::docker::runner::DockerRunner;
use cph::docker::state::RunnerState;

#[tokio::test]
async fn test_new_runner() {
    // 正常系
    let runner = DockerRunner::new(get_test_config_path(), "python").await;
    assert!(runner.is_ok());
    let runner = runner.unwrap();
    assert_eq!(runner.get_state().await.unwrap(), RunnerState::Ready);

    // 異常系: 無効な言語
    let runner = DockerRunner::new(get_test_config_path(), "invalid").await;
    assert!(runner.is_err());
}

#[tokio::test]
async fn test_runner_state_transitions() {
    let mut runner = DockerRunner::new(get_test_config_path(), "python").await.unwrap();
    
    // 初期状態
    assert_eq!(runner.get_state().await.unwrap(), RunnerState::Ready);
    
    // Ready -> Running
    runner.initialize("print('test')").await.unwrap();
    assert_eq!(runner.get_state().await.unwrap(), RunnerState::Running);
    
    // Running -> Stop
    runner.stop().await.unwrap();
    assert_eq!(runner.get_state().await.unwrap(), RunnerState::Stop);
}

#[tokio::test]
async fn test_invalid_state_transitions() {
    let mut runner = DockerRunner::new(get_test_config_path(), "python").await.unwrap();
    
    // Ready -> Stop (invalid)
    assert!(runner.stop().await.is_err());
    
    // Initialize
    runner.initialize("print('test')").await.unwrap();
    
    // Running -> Running (invalid: double initialize)
    assert!(runner.initialize("print('test')").await.is_err());
} 