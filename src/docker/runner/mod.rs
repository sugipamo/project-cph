use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;
use crate::config::Config;
use crate::docker::error::{DockerError, DockerResult};
use crate::docker::state::RunnerState;
use crate::docker::config::DockerConfig;
use crate::docker::fs::{DockerFileManager, DefaultDockerFileManager};
use crate::docker::executor::{DockerCommandExecutor, DefaultDockerExecutor};

pub struct DockerRunner {
    config: DockerConfig,
    file_manager: Box<dyn DockerFileManager>,
    executor: Box<dyn DockerCommandExecutor>,
    state: Arc<Mutex<RunnerState>>,
}

impl DockerRunner {
    pub fn new(config: Config, language: String) -> DockerResult<Self> {
        let docker_config = DockerConfig::new(&config, &language)?;
        
        Ok(Self {
            config: docker_config,
            file_manager: Box::new(DefaultDockerFileManager::new()),
            executor: Box::new(DefaultDockerExecutor::new()),
            state: Arc::new(Mutex::new(RunnerState::Ready)),
        })
    }

    pub fn from_language(language: &str) -> DockerResult<Self> {
        let config = Config::load()
            .map_err(|e| DockerError::Config(format!("設定の読み込みに失敗しました: {}", e)))?;
        
        Self::new(config, language.to_string())
    }

    pub async fn run_in_docker(&mut self, source_code: &str) -> DockerResult<String> {
        println!("Starting Docker execution");
        
        // イメージの確認と取得
        if !self.executor.check_image(self.config.image()).await? {
            if !self.executor.pull_image(self.config.image()).await? {
                *self.state.lock().await = RunnerState::Error;
                return Err(DockerError::Runtime(format!("イメージの取得に失敗: {}", self.config.image())));
            }
        }

        *self.state.lock().await = RunnerState::Running;

        // 一時ディレクトリの作成（ホスト側）
        let temp_dir = self.file_manager.create_temp_directory()?;
        
        // ソースファイルの作成（直接一時ディレクトリに配置）
        let source_file = self.file_manager.write_source_file(
            &temp_dir,
            &format!("main.{}", self.config.extension()),
            source_code,
        )?;

        // パーミッションの設定
        self.file_manager.set_permissions(&temp_dir, 0o755)?;
        self.file_manager.set_permissions(&source_file, 0o644)?;

        // コマンドの構築（シンプルに保つ）
        let command = if let Some(compile_cmd) = self.config.compile_cmd() {
            format!(
                "{} && {}",
                compile_cmd.join(" "),
                self.config.run_cmd().join(" ")
            )
        } else {
            self.config.run_cmd().join(" ")
        };

        // コンテナの実行
        let container_name = format!("runner-{}", Uuid::new_v4());
        let result = self.executor.run_container(
            &container_name,
            self.config.image(),
            self.config.memory_limit(),
            temp_dir.to_str().unwrap(),
            "/app",  // シンプルな固定マウントポイント
            &command,
            self.config.timeout_seconds(),
        ).await;

        // 一時ディレクトリの削除
        let _ = self.file_manager.cleanup(&temp_dir);

        // 状態の更新と結果の返却
        match result {
            Ok(output) => {
                *self.state.lock().await = RunnerState::Completed;
                Ok(output)
            }
            Err(e) => {
                *self.state.lock().await = RunnerState::Error;
                Err(e)
            }
        }
    }

    pub async fn cleanup(&mut self) -> DockerResult<()> {
        Ok(())
    }

    pub async fn get_state(&self) -> RunnerState {
        self.state.lock().await.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::docker::fs::MockDockerFileManager;
    use crate::docker::executor::MockDockerExecutor;

    #[tokio::test]
    async fn test_docker_runner_success() {
        let config = Config::load().unwrap();
        let docker_config = DockerConfig::new(&config, "rust").unwrap();
        
        let mut runner = DockerRunner {
            config: docker_config,
            file_manager: Box::new(MockDockerFileManager::new()),
            executor: Box::new(MockDockerExecutor::new(false)),
            state: Arc::new(Mutex::new(RunnerState::Ready)),
        };

        let result = runner.run_in_docker("fn main() { println!(\"Hello from Rust!\"); }").await;
        assert!(result.is_ok());
        if let Ok(output) = result {
            assert!(output.contains("Hello from Rust!"));
        }
        assert_eq!(runner.get_state().await, RunnerState::Completed);
    }

    #[tokio::test]
    async fn test_docker_runner_failure() {
        let config = Config::load().unwrap();
        let docker_config = DockerConfig::new(&config, "rust").unwrap();
        
        let mut runner = DockerRunner {
            config: docker_config,
            file_manager: Box::new(MockDockerFileManager::new()),
            executor: Box::new(MockDockerExecutor::new(true)),
            state: Arc::new(Mutex::new(RunnerState::Ready)),
        };

        let result = runner.run_in_docker("fn main() {}").await;
        assert!(result.is_err());
        assert_eq!(runner.get_state().await, RunnerState::Error);
    }
} 