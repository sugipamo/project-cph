use crate::docker::error::DockerResult;
use crate::docker::traits::{ContainerManager, IOHandler};
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
        async fn get_container_id(&self) -> DockerResult<String>;
    }
}

mock! {
    pub IOHandler {}
    #[async_trait::async_trait]
    impl IOHandler for IOHandler {
        async fn write(&self, input: &str) -> DockerResult<()>;
        async fn read_stdout(&self, timeout: Duration) -> DockerResult<String>;
        async fn read_stderr(&self, timeout: Duration) -> DockerResult<String>;
    }
} 