use anyhow::Result;
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct ContainerConfig {
    pub image: String,
    pub name: Option<String>,
    pub env: HashMap<String, String>,
    pub volumes: Vec<VolumeMount>,
    pub ports: Vec<PortMapping>,
    pub command: Option<Vec<String>>,
}

#[derive(Debug, Clone)]
pub struct VolumeMount {
    pub host_path: String,
    pub container_path: String,
    pub read_only: bool,
}

#[derive(Debug, Clone)]
pub struct PortMapping {
    pub host_port: u16,
    pub container_port: u16,
}

#[derive(Debug, Clone)]
pub struct ContainerInfo {
    pub id: String,
    pub name: String,
    pub status: String,
    pub image: String,
}

#[async_trait::async_trait]
pub trait Docker: Send + Sync {
    async fn create_container(&self, config: &ContainerConfig) -> Result<String>;
    async fn start_container(&self, container_id: &str) -> Result<()>;
    async fn stop_container(&self, container_id: &str) -> Result<()>;
    async fn remove_container(&self, container_id: &str) -> Result<()>;
    async fn list_containers(&self) -> Result<Vec<ContainerInfo>>;
    async fn exec_command(&self, container_id: &str, command: &[String]) -> Result<String>;
    async fn pull_image(&self, image: &str) -> Result<()>;
}