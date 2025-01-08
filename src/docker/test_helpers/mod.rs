use crate::docker::execution::{DockerCommand, CommandOutput};
use mockall::automock;
use async_trait::async_trait;
use anyhow::Result;

#[automock]
#[async_trait]
pub trait TestDockerCommandExecutor: Send + Sync {
    async fn execute(&self, command: DockerCommand) -> Result<CommandOutput>;
}

#[automock]
#[async_trait]
pub trait TestContainerManager: Send + Sync {
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> Result<()>;
    async fn start_container(&mut self) -> Result<()>;
    async fn stop_container(&mut self) -> Result<()>;
    async fn get_container_id(&self) -> Result<String>;
    async fn get_exit_code(&self) -> Result<i32>;
    async fn check_image(&self, image: &str) -> Result<bool>;
    async fn pull_image(&self, image: &str) -> Result<()>;
}

#[automock]
#[async_trait]
pub trait TestCompilationManager: Send + Sync {
    async fn compile<'a>(&mut self, source_code: &str, compile_cmd: Option<&'a [String]>, env_vars: &[String]) -> Result<()>;
    async fn get_compilation_output(&self) -> Result<(String, String)>;
} 