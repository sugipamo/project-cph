use std::sync::Arc;
use tokio::sync::Mutex;
use bollard::Docker;
use bollard::container::{Config as DockerConfig, CreateContainerOptions, HostConfig};
use bollard::exec::{CreateExecOptions, StartExecOptions};
use thiserror::Error;
use crate::docker::state::RunnerState;
use crate::config::Config;

// New error type
#[derive(Error, Debug)]
pub enum CompilerError {
    #[error("Failed to resolve language: {0}")]
    LanguageResolution(String),
    #[error("Container creation failed: {0}")]
    ContainerCreation(String),
    #[error("Container startup failed: {0}")]
    ContainerStartup(String),
    #[error("Configuration error: {0}")]
    Config(String),
}

// New trait for compilation operations
pub trait CompilationManager {
    async fn compile(&mut self, language: &str) -> Result<(), CompilerError>;
    async fn cleanup(&mut self) -> Result<(), CompilerError>;
}

// New trait for container operations
pub trait ContainerManager {
    async fn create_container(&mut self, config: DockerConfig) -> Result<String, CompilerError>;
    async fn start_container(&mut self, container_id: &str) -> Result<(), CompilerError>;
}

pub(super) struct DockerCompiler {
    docker: Docker,
    container_id: String,
    config: Arc<Config>,
    state: Arc<Mutex<RunnerState>>,
    stdout_buffer: Arc<Mutex<Vec<String>>>,
    stderr_buffer: Arc<Mutex<Vec<String>>>,
}

impl DockerCompiler {
    pub(super) fn new(
        docker: Docker,
        config: Config,
        state: Arc<Mutex<RunnerState>>,
        stdout_buffer: Arc<Mutex<Vec<String>>>,
        stderr_buffer: Arc<Mutex<Vec<String>>>,
    ) -> Self {
        Self {
            docker,
            container_id: String::new(),
            config: Arc::new(config),
            state,
            stdout_buffer,
            stderr_buffer,
        }
    }
}

impl CompilationManager for DockerCompiler {
    async fn compile(&mut self, language: &str) -> Result<(), CompilerError> {
        let resolved_lang = self.config
            .get_with_alias::<String>(&format!("{}.name", language))
            .map_err(|e| CompilerError::LanguageResolution(e.to_string()))?;

        // ... rest of compilation logic, now using proper error types ...
        Ok(())
    }

    async fn cleanup(&mut self) -> Result<(), CompilerError> {
        // Add cleanup implementation
        Ok(())
    }
}

impl ContainerManager for DockerCompiler {
    async fn create_container(&mut self, config: DockerConfig) -> Result<String, CompilerError> {
        // Implementation moved from compile method
        Ok(String::new())
    }

    async fn start_container(&mut self, container_id: &str) -> Result<(), CompilerError> {
        // Implementation moved from compile method
        Ok(())
    }
}

// ... rest of existing implementation ...