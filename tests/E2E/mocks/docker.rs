use mockall::automock;
use std::path::PathBuf;
use async_trait::async_trait;

#[automock]
#[async_trait]
pub trait DockerRunner {
    async fn run_in_docker(&mut self, source_code: &str) -> Result<RunOutput, String>;
    async fn write(&mut self, input: &str) -> Result<(), String>;
    async fn read(&mut self) -> Result<String, String>;
    async fn read_error(&mut self) -> Result<String, String>;
    async fn stop(&mut self) -> Result<(), String>;
}

pub struct RunOutput {
    pub stdout: String,
    pub stderr: String,
}

/// テスト用のDockerランナー
pub struct TestDockerRunner {
    test_dir: PathBuf,
}

#[async_trait]
impl DockerRunner for TestDockerRunner {
    async fn run_in_docker(&mut self, source_code: &str) -> Result<RunOutput, String> {
        Ok(RunOutput {
            stdout: "".to_string(),
            stderr: "".to_string(),
        })
    }

    async fn write(&mut self, input: &str) -> Result<(), String> {
        Ok(())
    }

    async fn read(&mut self) -> Result<String, String> {
        Ok("1\n".to_string())
    }

    async fn read_error(&mut self) -> Result<String, String> {
        Ok("".to_string())
    }

    async fn stop(&mut self) -> Result<(), String> {
        Ok(())
    }
}

impl TestDockerRunner {
    pub fn new(test_dir: PathBuf) -> Self {
        Self { test_dir }
    }

    /// テストケースを設定
    pub fn set_test_case(&mut self, input: &str, expected_output: &str) {
        // テストケースのファイルを作成
        let test_dir = self.test_dir.join("active_contest/test/a");
        std::fs::create_dir_all(&test_dir).unwrap();
        
        std::fs::write(test_dir.join("sample1.in"), input).unwrap();
        std::fs::write(test_dir.join("sample1.out"), expected_output).unwrap();
    }
} 