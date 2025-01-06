use crate::docker::error::DockerResult;
use crate::docker::traits::{ContainerManager, IOHandler, CompilationManager};
use crate::config::Config;
use std::time::Duration;
use mockall::mock;
use mockall::predicate::*;

// モックの定義
mock! {
    pub ContainerManager {}
    #[async_trait::async_trait]
    impl ContainerManager for ContainerManager {
        async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> DockerResult<()>;
        async fn start_container(&mut self) -> DockerResult<()>;
        async fn stop_container(&mut self) -> DockerResult<()>;
        async fn check_image(&self, image: &str) -> DockerResult<bool>;
        async fn pull_image(&self, image: &str) -> DockerResult<()>;
    }
}

mock! {
    pub IOHandler {}
    #[async_trait::async_trait]
    impl IOHandler for IOHandler {
        async fn write(&self, input: &str) -> DockerResult<()>;
        async fn read_stdout(&self, timeout: Duration) -> DockerResult<String>;
        async fn read_stderr(&self, timeout: Duration) -> DockerResult<String>;
        async fn setup_io(&mut self) -> DockerResult<()>;
    }
}

mock! {
    pub CompilationManager {}
    #[async_trait::async_trait]
    impl CompilationManager for CompilationManager {
        async fn compile(&mut self, source_code: &str, compile_cmd: Option<Vec<String>>, env_vars: Vec<String>) -> DockerResult<()>;
        async fn get_compilation_output(&self) -> DockerResult<(String, String)>;
    }
}

// テストヘルパー構造体
pub struct TestHelper {
    pub container_manager: MockContainerManager,
    pub io_handler: MockIOHandler,
    pub compilation_manager: MockCompilationManager,
}

impl TestHelper {
    pub fn new() -> Self {
        Self {
            container_manager: MockContainerManager::new(),
            io_handler: MockIOHandler::new(),
            compilation_manager: MockCompilationManager::new(),
        }
    }

    pub fn setup_success_expectations(&mut self) {
        self.container_manager
            .expect_check_image()
            .returning(|_| Ok(true));
        
        self.container_manager
            .expect_create_container()
            .returning(|_, _, _| Ok(()));
        
        self.container_manager
            .expect_start_container()
            .returning(|| Ok(()));

        self.io_handler
            .expect_setup_io()
            .returning(|| Ok(()));
        
        self.io_handler
            .expect_read_stdout()
            .returning(|_| Ok("Test output".to_string()));
        
        self.io_handler
            .expect_read_stderr()
            .returning(|_| Ok("".to_string()));
    }

    pub fn setup_compilation_expectations(&mut self) {
        self.compilation_manager
            .expect_compile()
            .returning(|_, _, _| Ok(()));
        
        self.compilation_manager
            .expect_get_compilation_output()
            .returning(|| Ok(("".to_string(), "".to_string())));
    }
}

// テスト用の設定ヘルパー
pub fn create_test_config() -> Config {
    let mut config = Config::new();
    config.set("system.docker.timeout_seconds", 30).unwrap();
    config.set("system.docker.memory_limit", 512).unwrap();
    config
} 