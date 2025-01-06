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
    use mockall::predicate::*;
    use mockall::mock;
    use std::time::Duration;

    mock! {
        ContainerManager {}
        #[async_trait]
        impl ContainerManager for ContainerManager {
            async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> DockerResult<()>;
            async fn start_container(&mut self) -> DockerResult<()>;
            async fn stop_container(&mut self) -> DockerResult<()>;
            async fn check_image(&self, image: &str) -> DockerResult<bool>;
            async fn pull_image(&self, image: &str) -> DockerResult<()>;
        }
    }

    mock! {
        IOHandler {}
        #[async_trait]
        impl IOHandler for IOHandler {
            async fn write(&self, input: &str) -> DockerResult<()>;
            async fn read_stdout(&self, timeout: Duration) -> DockerResult<String>;
            async fn read_stderr(&self, timeout: Duration) -> DockerResult<String>;
            async fn setup_io(&mut self) -> DockerResult<()>;
        }
    }

    mock! {
        CompilationManager {}
        #[async_trait]
        impl CompilationManager for CompilationManager {
            async fn compile(&mut self, source_code: &str, compile_cmd: Option<Vec<String>>, env_vars: Vec<String>) -> DockerResult<()>;
            async fn get_compilation_output(&self) -> DockerResult<(String, String)>;
        }
    }

    #[tokio::test]
    async fn test_docker_runner_success() {
        let mut mock_container = MockContainerManager::new();
        let mut mock_io = MockIOHandler::new();
        let mut mock_compiler = MockCompilationManager::new();

        mock_container
            .expect_check_image()
            .return_once(|_| Ok(true));
        
        mock_container
            .expect_create_container()
            .return_once(|_, _, _| Ok(()));
        
        mock_container
            .expect_start_container()
            .return_once(|| Ok(()));

        mock_io
            .expect_setup_io()
            .return_once(|| Ok(()));
        
        mock_io
            .expect_read_stdout()
            .return_once(|_| Ok("Hello from test!".to_string()));
        
        mock_io
            .expect_read_stderr()
            .return_once(|_| Ok("".to_string()));

        let config = Config::load().unwrap();
        let mut runner = DockerRunner::new(
            config,
            Box::new(mock_container),
            Box::new(mock_io),
            Box::new(mock_compiler),
        );

        let result = runner.run_in_docker("test code").await;
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "Hello from test!");
        assert_eq!(runner.get_state().await, RunnerState::Completed);
    }
} 