use std::path::PathBuf;

#[derive(Debug, Clone)]
pub struct ContainerConfig {
    pub id: String,
    pub image: String,
    pub working_dir: PathBuf,
    pub command: Vec<String>,
    pub env_vars: Vec<String>,
} 