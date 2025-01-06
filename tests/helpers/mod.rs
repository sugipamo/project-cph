use std::fs;
use cph::config::Config;
use tempfile::TempDir;
use std::env;
use std::path::Path;
use std::process::Command;
use std::sync::Arc;
use tokio::sync::Mutex;
use async_trait::async_trait;
use std::collections::HashMap;

use crate::docker::error::{DockerError, DockerResult};
use crate::docker::traits::DockerCommandExecutor;

thread_local! {
    static TEST_DIR: std::cell::RefCell<Option<TempDir>> = std::cell::RefCell::new(None);
}

pub fn setup() {
    // テスト用の一時ディレクトリを作成
    let temp_dir = TempDir::new().unwrap();
    let temp_path = temp_dir.path().to_path_buf();

    // テスト用のディレクトリを作成
    fs::create_dir_all(temp_path.join("test-rust")).unwrap();
    fs::create_dir_all(temp_path.join("test-pypy")).unwrap();
    fs::create_dir_all(temp_path.join("test-cpp")).unwrap();

    // テスト用の環境変数を設定
    env::set_var("CPH_TEST_DIR", temp_path.join("test").to_str().unwrap());
    env::set_var("CPH_ACTIVE_DIR", temp_path.to_str().unwrap());

    // テスト用の設定を読み込む
    let _config = Config::load().unwrap();

    // 一時ディレクトリを保存
    TEST_DIR.with(|test_dir| {
        *test_dir.borrow_mut() = Some(temp_dir);
    });
}

pub fn teardown() {
    // 一時ディレクトリは自動的に削除されるため、
    // 明示的な削除処理は不要です
    TEST_DIR.with(|test_dir| {
        test_dir.borrow_mut().take();
    });
}

#[derive(Default)]
pub struct MockDockerCommandExecutor {
    responses: Arc<Mutex<HashMap<String, (bool, String, String)>>>,
}

impl MockDockerCommandExecutor {
    pub fn new() -> Self {
        Self {
            responses: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub async fn set_response(&self, args: Vec<String>, response: (bool, String, String)) {
        let key = args.join(" ");
        self.responses.lock().await.insert(key, response);
    }
}

#[async_trait]
impl DockerCommandExecutor for MockDockerCommandExecutor {
    async fn execute_command(&self, args: Vec<String>) -> DockerResult<(bool, String, String)> {
        let key = args.join(" ");
        let responses = self.responses.lock().await;
        
        match responses.get(&key) {
            Some(response) => Ok(response.clone()),
            None => Err(DockerError::Container(format!(
                "モックレスポンスが設定されていません: {}",
                key
            ))),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_mock_docker_command_executor() {
        let executor = MockDockerCommandExecutor::new();
        
        // テストレスポンスを設定
        executor
            .set_response(
                vec!["create".to_string(), "-i".to_string()],
                (true, "container_id".to_string(), String::new()),
            )
            .await;

        // 正常系のテスト
        let result = executor
            .execute_command(vec!["create".to_string(), "-i".to_string()])
            .await;
        assert!(result.is_ok());
        let (success, stdout, _) = result.unwrap();
        assert!(success);
        assert_eq!(stdout, "container_id");

        // 未設定のコマンドのテスト
        let result = executor
            .execute_command(vec!["unknown".to_string()])
            .await;
        assert!(result.is_err());
    }
} 