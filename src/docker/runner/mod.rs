use std::sync::Arc;
use tokio::sync::Mutex;
use crate::config::Config;
use crate::docker::error::{DockerError, DockerResult};
use crate::docker::state::RunnerState;
use crate::docker::traits::{ContainerManager, IOHandler, CompilationManager};

pub mod default_impl;

pub struct DockerRunner {
    container_manager: Box<dyn ContainerManager>,
    io_handler: Box<dyn IOHandler>,
    compilation_manager: Box<dyn CompilationManager>,
    config: Config,
    state: Arc<Mutex<RunnerState>>,
}

impl DockerRunner {
    pub fn new(
        config: Config,
        container_manager: Box<dyn ContainerManager>,
        io_handler: Box<dyn IOHandler>,
        compilation_manager: Box<dyn CompilationManager>,
    ) -> Self {
        Self {
            container_manager,
            io_handler,
            compilation_manager,
            config,
            state: Arc::new(Mutex::new(RunnerState::Ready)),
        }
    }

    pub async fn run_in_docker(&mut self, source_code: &str) -> DockerResult<String> {
        println!("Starting Docker execution");
        
        let image = self.config.get_image()?;
        
        // イメージの確認と取得
        if !self.container_manager.check_image(&image).await? {
            self.container_manager.pull_image(&image).await?;
        }

        *self.state.lock().await = RunnerState::Running;

        // コンパイルが必要な場合は実行
        if let Some(compile_cmd) = self.config.get_compile_cmd()? {
            self.compilation_manager.compile(
                source_code,
                Some(compile_cmd),
                self.config.get_env_vars()?,
            ).await?;
        }

        // コンテナの作成と起動
        self.container_manager.create_container(
            &image,
            self.config.get_run_cmd()?,
            &self.config.get_working_dir()?,
        ).await?;

        self.container_manager.start_container().await?;
        
        // I/O設定
        self.io_handler.setup_io().await?;

        // 実行結果の取得
        let timeout = self.config.get_timeout()?;
        let output = self.io_handler.read_stdout(timeout).await?;
        let stderr = self.io_handler.read_stderr(timeout).await?;

        if !stderr.is_empty() {
            println!("Warning: stderr not empty: {}", stderr);
        }

        *self.state.lock().await = RunnerState::Completed;
        Ok(output)
    }

    pub async fn cleanup(&mut self) -> DockerResult<()> {
        self.container_manager.stop_container().await
    }

    pub async fn get_state(&self) -> RunnerState {
        self.state.lock().await.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::docker::runner::test_helpers::{TestHelper, create_test_config};
    use tokio::time::Duration;

    #[tokio::test]
    async fn test_docker_runner_basic_success() {
        let mut helper = TestHelper::new();
        helper.setup_success_expectations();

        let config = create_test_config();
        let mut runner = DockerRunner::new(
            config,
            Box::new(helper.container_manager),
            Box::new(helper.io_handler),
            Box::new(helper.compilation_manager),
        );

        let result = runner.run_in_docker("test code").await;
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "Test output");
        assert_eq!(runner.get_state().await, RunnerState::Completed);
    }

    #[tokio::test]
    async fn test_docker_runner_with_compilation() {
        let mut helper = TestHelper::new();
        helper.setup_success_expectations();
        helper.setup_compilation_expectations();

        let mut config = create_test_config();
        config.set("languages.test.compile_cmd", vec!["gcc", "-o", "test"]).unwrap();

        let mut runner = DockerRunner::new(
            config,
            Box::new(helper.container_manager),
            Box::new(helper.io_handler),
            Box::new(helper.compilation_manager),
        );

        let result = runner.run_in_docker("test code").await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_docker_runner_image_pull() {
        let mut helper = TestHelper::new();
        helper.container_manager
            .expect_check_image()
            .returning(|_| Ok(false));
        
        helper.container_manager
            .expect_pull_image()
            .returning(|_| Ok(()));

        helper.setup_success_expectations();

        let config = create_test_config();
        let mut runner = DockerRunner::new(
            config,
            Box::new(helper.container_manager),
            Box::new(helper.io_handler),
            Box::new(helper.compilation_manager),
        );

        let result = runner.run_in_docker("test code").await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_docker_runner_cleanup() {
        let mut helper = TestHelper::new();
        helper.setup_success_expectations();
        helper.container_manager
            .expect_stop_container()
            .returning(|| Ok(()));

        let config = create_test_config();
        let mut runner = DockerRunner::new(
            config,
            Box::new(helper.container_manager),
            Box::new(helper.io_handler),
            Box::new(helper.compilation_manager),
        );

        let run_result = runner.run_in_docker("test code").await;
        assert!(run_result.is_ok());

        let cleanup_result = runner.cleanup().await;
        assert!(cleanup_result.is_ok());
    }

    #[tokio::test]
    async fn test_docker_runner_error_handling() {
        let mut helper = TestHelper::new();
        helper.container_manager
            .expect_check_image()
            .returning(|_| Ok(true));
        
        helper.container_manager
            .expect_create_container()
            .returning(|_, _, _| Err(DockerError::Container("Test error".to_string())));

        let config = create_test_config();
        let mut runner = DockerRunner::new(
            config,
            Box::new(helper.container_manager),
            Box::new(helper.io_handler),
            Box::new(helper.compilation_manager),
        );

        let result = runner.run_in_docker("test code").await;
        assert!(result.is_err());
        assert_eq!(runner.get_state().await, RunnerState::Error);
    }
} 