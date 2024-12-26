use std::path::Path;
use std::process::Command;
use std::time::Duration;
use tokio::process::Command as TokioCommand;
use tokio::io::AsyncWriteExt;
use std::process::Stdio;
use tokio::time::timeout;
use toml::Value;
use once_cell::sync::Lazy;

use crate::Error;

const DEFAULT_RUST_IMAGE: &str = "rust:1.70";
const DEFAULT_PYPY_IMAGE: &str = "pypy:3.10";
const DEFAULT_TIMEOUT_SECS: u64 = 5;
const DEFAULT_MEMORY_LIMIT: &str = "512m";

static DOCKER_CONFIG: Lazy<DockerConfig> = Lazy::new(|| {
    DockerConfig::load().expect("Failed to load Docker config")
});

pub struct DockerConfig {
    pub rust_image: String,
    pub pypy_image: String,
    pub timeout_seconds: u64,
    pub memory_limit: String,
}

impl DockerConfig {
    fn load() -> Result<Self, Error> {
        let config = std::fs::read_to_string("config/docker.toml")
            .map_err(|e| Error::test_execution(format!("Failed to read docker config: {}", e)))?;
        
        let config: Value = toml::from_str(&config)
            .map_err(|e| Error::test_execution(format!("Failed to parse docker config: {}", e)))?;
        
        let images = &config["images"];
        let runtime = &config["runtime"];
        
        Ok(Self {
            rust_image: images["rust"].as_str().unwrap_or(DEFAULT_RUST_IMAGE).to_string(),
            pypy_image: images["pypy"].as_str().unwrap_or(DEFAULT_PYPY_IMAGE).to_string(),
            timeout_seconds: runtime["timeout_seconds"].as_integer().unwrap_or(DEFAULT_TIMEOUT_SECS as i64) as u64,
            memory_limit: runtime["memory_limit"].as_str().unwrap_or(DEFAULT_MEMORY_LIMIT).to_string(),
        })
    }

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
) -> Result<(String, String), Error> {
    let mut command = TokioCommand::new(program);
    command.args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let mut child = command.spawn()
        .map_err(|e| Error::test_execution(format!("Failed to spawn process: {}", e)))?;

    if let Some(input) = stdin {
        if let Some(mut stdin) = child.stdin.take() {
            if let Err(e) = stdin.write_all(input.as_bytes()).await {
                return Err(Error::test_execution(format!("Failed to write to stdin: {}", e)));
            }
        }
    }

    let config = DockerConfig::get();
    match timeout(Duration::from_secs(config.timeout_seconds), child.wait_with_output()).await {
        Ok(Ok(output)) => Ok((
            String::from_utf8_lossy(&output.stdout).into_owned(),
            String::from_utf8_lossy(&output.stderr).into_owned(),
        )),
        Ok(Err(e)) => Err(Error::test_execution(format!("Execution failed: {}", e))),
        Err(_) => Err(Error::TestTimeout),
    }
}

pub fn run_in_docker(
    workspace_dir: &Path,
    image: &str,
    cmd: &[&str],
) -> Result<std::process::Output, Error> {
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
        .map_err(|e| Error::test_execution(format!("Failed to run docker: {}", e)))
} 