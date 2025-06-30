use crate::infrastructure::test_support::{Expectation, Mock};
use anyhow::Result;
use std::collections::HashMap;

#[derive(Default)]
pub struct MockDocker {
    containers: HashMap<String, ContainerInfo>,
    images: Vec<String>,
    run_responses: HashMap<String, RunResponse>,
    expectations: Vec<Expectation>,
}

#[derive(Clone, Debug)]
pub struct ContainerInfo {
    pub id: String,
    pub image: String,
    pub status: ContainerStatus,
    pub ports: HashMap<u16, u16>,
}

#[derive(Clone, Debug, PartialEq)]
pub enum ContainerStatus {
    Running,
    Stopped,
    Exited(i32),
}

#[derive(Clone, Debug)]
pub struct RunResponse {
    pub container_id: String,
    pub exit_code: i32,
    pub stdout: String,
    pub stderr: String,
}

impl MockDocker {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_image(mut self, image: impl Into<String>) -> Self {
        self.images.push(image.into());
        self
    }

    pub fn with_container(mut self, id: impl Into<String>, info: ContainerInfo) -> Self {
        self.containers.insert(id.into(), info);
        self
    }

    pub fn with_run_response(mut self, key: impl Into<String>, response: RunResponse) -> Self {
        self.run_responses.insert(key.into(), response);
        self
    }

    pub async fn run_container(
        &mut self,
        image: &str,
        command: &[String],
        _working_dir: Option<&str>,
    ) -> Result<RunResponse> {
        if let Some(expectation) = self.expectations.first() {
            expectation.call();
        }

        let key = format!("{}:{}", image, command.join(" "));
        
        self.run_responses
            .get(&key)
            .cloned()
            .or_else(|| {
                Some(RunResponse {
                    container_id: format!("mock-container-{}", uuid::Uuid::new_v4()),
                    exit_code: 0,
                    stdout: String::new(),
                    stderr: String::new(),
                })
            })
            .ok_or_else(|| anyhow::anyhow!("No response configured"))
    }

    pub async fn pull_image(&mut self, image: &str) -> Result<()> {
        if !self.images.contains(&image.to_string()) {
            self.images.push(image.to_string());
        }
        Ok(())
    }

    pub async fn remove_container(&mut self, id: &str) -> Result<()> {
        self.containers.remove(id);
        Ok(())
    }

    pub fn expect_run(&mut self) -> &mut Expectation {
        let expectation = Expectation::new();
        self.expectations.push(expectation);
        self.expectations.last_mut().unwrap()
    }
}

impl Mock<()> for MockDocker {
    fn expect(&mut self) -> &mut Expectation {
        self.expect_run()
    }

    fn checkpoint(&mut self) {
        self.expectations.clear();
    }

    fn verify(&self) -> Result<()> {
        for expectation in &self.expectations {
            expectation.verify()?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_mock_docker_run() -> Result<()> {
        let mut docker = MockDocker::new()
            .with_run_response(
                "ubuntu:echo hello",
                RunResponse {
                    container_id: "test-123".to_string(),
                    exit_code: 0,
                    stdout: "hello\n".to_string(),
                    stderr: String::new(),
                },
            );

        let response = docker
            .run_container("ubuntu", &["echo".to_string(), "hello".to_string()], None)
            .await?;

        assert_eq!(response.container_id, "test-123");
        assert_eq!(response.exit_code, 0);
        assert_eq!(response.stdout, "hello\n");

        Ok(())
    }

    #[tokio::test]
    async fn test_mock_docker_pull() -> Result<()> {
        let mut docker = MockDocker::new();
        
        docker.pull_image("alpine:latest").await?;
        
        assert!(docker.images.contains(&"alpine:latest".to_string()));
        
        Ok(())
    }

    #[tokio::test]
    async fn test_mock_docker_expectations() -> Result<()> {
        let mut docker = MockDocker::new();
        
        docker.expect_run().times(2);
        
        docker.run_container("test", &[], None).await?;
        docker.run_container("test", &[], None).await?;
        
        docker.verify()?;
        Ok(())
    }
}