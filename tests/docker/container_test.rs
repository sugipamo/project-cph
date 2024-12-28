use super::get_test_config_path;
use cph::docker::runner::DockerRunner;
use cph::docker::state::RunnerState;
use tokio::time::sleep;
use std::time::Duration;

#[tokio::test]
async fn test_python_container() {
    let mut runner = DockerRunner::new(get_test_config_path(), "python").await.unwrap();
    
    // Pythonプログラムの実行
    runner.initialize("print('Hello, World!')").await.unwrap();
    sleep(Duration::from_millis(100)).await;
    
    let output = runner.read().await.unwrap();
    assert_eq!(output.trim(), "Hello, World!");
    
    runner.stop().await.unwrap();
}

#[tokio::test]
async fn test_cpp_container() {
    let mut runner = DockerRunner::new(get_test_config_path(), "cpp").await.unwrap();
    
    // C++プログラムの実行（コンパイルエラー）
    let result = runner.initialize("invalid cpp code").await;
    assert!(result.is_err());
    assert_eq!(runner.get_state().await.unwrap(), RunnerState::Error);
    
    // 正常なC++プログラム
    let mut runner = DockerRunner::new(get_test_config_path(), "cpp").await.unwrap();
    runner.initialize(r#"
        #include <iostream>
        int main() {
            std::cout << "Hello, C++!" << std::endl;
            return 0;
        }
    "#).await.unwrap();
    
    sleep(Duration::from_millis(100)).await;
    let output = runner.read().await.unwrap();
    assert_eq!(output.trim(), "Hello, C++!");
}

#[tokio::test]
async fn test_rust_container() {
    let mut runner = DockerRunner::new(get_test_config_path(), "rust").await.unwrap();
    
    // Rustプログラムの実行
    runner.initialize(r#"
        fn main() {
            println!("Hello, Rust!");
        }
    "#).await.unwrap();
    
    sleep(Duration::from_millis(100)).await;
    let output = runner.read().await.unwrap();
    assert_eq!(output.trim(), "Hello, Rust!");
} 