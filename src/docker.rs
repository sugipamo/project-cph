use std::path::Path;
use std::process::Command;
use std::time::Duration;
use tokio::process::Command as TokioCommand;
use tokio::io::AsyncWriteExt;
use std::process::Stdio;
use tokio::time::timeout;
use once_cell::sync::Lazy;
use thiserror::Error;

use crate::Error as CrateError;
use crate::{DEFAULT_RUST_IMAGE, DEFAULT_PYPY_IMAGE, DEFAULT_TIMEOUT_SECS, DEFAULT_MEMORY_LIMIT};

#[derive(Debug, Error)]
pub enum DockerError {
    #[error("Docker command failed: {0}")]
    CommandFailed(String),
    
    #[error("Docker execution error: {0}")]
    Execution(String),
    
    #[error("Docker timeout after {0} seconds")]
    Timeout(u64),
}

impl DockerError {
    fn failed(operation: &str, error: impl std::fmt::Display) -> Self {
        DockerError::Execution(format!("Failed to {}: {}", operation, error))
    }
}

static DOCKER_CONFIG: Lazy<DockerConfig> = Lazy::new(|| DockerConfig {
    rust_image: DEFAULT_RUST_IMAGE.to_string(),
    pypy_image: DEFAULT_PYPY_IMAGE.to_string(),
    timeout_seconds: DEFAULT_TIMEOUT_SECS,
    memory_limit: DEFAULT_MEMORY_LIMIT.to_string(),
});

pub struct DockerConfig {
    pub rust_image: String,
    pub pypy_image: String,
    pub timeout_seconds: u64,
    pub memory_limit: String,
}

impl DockerConfig {
    pub fn get() -> &'static Self {
        &DOCKER_CONFIG
    }

    pub fn get_image(&self, language: &str) -> String {
        match language.to_lowercase().as_str() {
            "rust" | "r" => self.rust_image.clone(),
            "pypy" | "py" => self.pypy_image.clone(),
            _ => self.rust_image.clone(),
        }
    }
}

pub async fn execute_program(
    program: &str,
    args: &[&str],
    stdin: Option<String>,
) -> Result<(String, String), CrateError> {
    let mut command = TokioCommand::new(program);
    command.args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let mut child = command.spawn()
        .map_err(|e| CrateError::Docker(DockerError::failed("spawn process", e)))?;

    if let Some(input) = stdin {
        if let Some(mut stdin) = child.stdin.take() {
            if let Err(e) = stdin.write_all(input.as_bytes()).await {
                return Err(CrateError::Docker(DockerError::failed("write to stdin", e)));
            }
        }
    }

    let config = DockerConfig::get();
    match timeout(Duration::from_secs(config.timeout_seconds), child.wait_with_output()).await {
        Ok(Ok(output)) => Ok((
            String::from_utf8_lossy(&output.stdout).into_owned(),
            String::from_utf8_lossy(&output.stderr).into_owned(),
        )),
        Ok(Err(e)) => Err(CrateError::Docker(DockerError::failed("execute program", e))),
        Err(_) => Err(CrateError::Docker(DockerError::Timeout(config.timeout_seconds))),
    }
}

pub fn run_in_docker(
    workspace_dir: &Path,
    image: &str,
    cmd: &[&str],
) -> Result<std::process::Output, CrateError> {
    let config = DockerConfig::get();
    Command::new("docker")
        .args([
            "run",
            "--rm",
            "--memory",
            &config.memory_limit,
            "--memory-swap",
            &config.memory_limit,
            "-v",
            &format!("{}:/workspace", workspace_dir.display()),
            "-w",
            "/workspace",
            image,
        ])
        .args(cmd)
        .output()
        .map_err(|e| CrateError::Docker(DockerError::failed("run docker", e)))
} 