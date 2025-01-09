pub mod command;
pub mod compilation;
pub mod container;

pub use command::Executor;
pub use compilation::Compiler;
pub use container::Runtime;

use anyhow::Result;
use std::time::Duration;
use async_trait::async_trait;
use crate::docker::config::Config;

#[derive(Debug)]
pub struct CommandOutput {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
}

impl CommandOutput {
    #[must_use = "この関数は新しいCommandOutputインスタンスを返します"]
    pub const fn new(stdout: String, stderr: String, exit_code: i32) -> Self {
        Self {
            stdout,
            stderr,
            exit_code,
        }
    }
}

#[async_trait]
pub trait CommandExecutor {
    async fn execute(&self, command: Executor) -> Result<CommandOutput>;
}

/// Dockerコンテナの実行操作を提供するトレイト
#[async_trait]
pub trait Operations: Send + Sync {
    async fn initialize(&mut self, config: Config) -> Result<()>;
    async fn start(&mut self) -> Result<()>;
    async fn stop(&mut self) -> Result<()>;
    async fn execute(&mut self, command: &str) -> Result<(String, String)>;
    async fn write(&mut self, input: &str) -> Result<()>;
    async fn read_stdout(&mut self, timeout: Duration) -> Result<String>;
    async fn read_stderr(&mut self, timeout: Duration) -> Result<String>;
}

/// コンパイル操作を提供するトレイト
#[async_trait]
pub trait CompilerOperations: Send + Sync {
    async fn compile(
        &mut self,
        source_code: &str,
        compile_cmd: Option<Vec<String>>,
        env_vars: Vec<String>,
    ) -> Result<()>;
    async fn get_compilation_output(&self) -> Result<(String, String)>;
}

/// Dockerコンテナのランタイム管理を行うトレイト
#[async_trait]
pub trait RuntimeManager: Send + Sync {
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> Result<()>;
    async fn start_container(&mut self) -> Result<()>;
    async fn stop_container(&mut self) -> Result<()>;
    async fn get_container_id(&self) -> Result<String>;
    async fn get_exit_code(&self) -> Result<i32>;
    async fn check_image(&self, image: &str) -> Result<bool>;
    async fn pull_image(&self, image: &str) -> Result<()>;
} 