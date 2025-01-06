use crate::docker::error::DockerResult;
use crate::docker::execution::{DockerCommand, CommandOutput};
use mockall::automock;

#[allow(async_fn_in_trait)]
#[automock]
pub trait TestDockerCommandExecutor: Send + Sync {
    async fn execute(&self, command: DockerCommand) -> DockerResult<CommandOutput>;
}

#[allow(async_fn_in_trait)]
#[automock]
pub trait TestContainerManager: Send + Sync {
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> DockerResult<()>;
    async fn start_container(&mut self) -> DockerResult<()>;
    async fn stop_container(&mut self) -> DockerResult<()>;
    async fn get_container_id(&self) -> DockerResult<String>;
    async fn get_exit_code(&self) -> DockerResult<i32>;
    async fn check_image(&self, image: &str) -> DockerResult<bool>;
    async fn pull_image(&self, image: &str) -> DockerResult<()>;
}

#[allow(async_fn_in_trait)]
#[automock]
pub trait TestCompilationManager: Send + Sync {
    async fn compile(&mut self, source_code: &str, compile_cmd: Option<Vec<String>>, env_vars: Vec<String>) -> DockerResult<()>;
    async fn get_compilation_output(&self) -> DockerResult<(String, String)>;
} 