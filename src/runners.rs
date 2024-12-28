use async_trait::async_trait;
use bollard::container::{Config, CreateContainerOptions, StartContainerOptions};
use bollard::exec::{CreateExecOptions, StartExecResults};
use bollard::Docker;
use futures::StreamExt;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::{Duration, timeout};

#[derive(Debug, Clone, PartialEq)]
pub enum RunnerState {
    Ready,
    Running,
    Stop,
    Error,
}

pub struct DockerRunner {
    docker: Docker,
    container_id: String,
    state: Arc<Mutex<RunnerState>>,
    stdout_buffer: Arc<Mutex<Vec<String>>>,
    stderr_buffer: Arc<Mutex<Vec<String>>>,
    config: RunnerConfig,
}

pub struct RunnerConfig {
    timeout_seconds: u64,
    memory_limit_mb: i64,
    image_name: String,
}

impl Default for RunnerConfig {
    fn default() -> Self {
        Self {
            timeout_seconds: 5,
            memory_limit_mb: 128,
            image_name: "python:3.9-slim".to_string(),
        }
    }
}

impl DockerRunner {
    pub async fn new(config: RunnerConfig) -> Result<Self, Box<dyn std::error::Error>> {
        let docker = Docker::connect_with_local_defaults()?;
        let state = Arc::new(Mutex::new(RunnerState::Ready));
        let stdout_buffer = Arc::new(Mutex::new(Vec::new()));
        let stderr_buffer = Arc::new(Mutex::new(Vec::new()));

        Ok(Self {
            docker,
            container_id: String::new(),
            state,
            stdout_buffer,
            stderr_buffer,
            config,
        })
    }

    pub async fn initialize(&mut self, source_code: &str) -> Result<(), Box<dyn std::error::Error>> {
        // イメージのプル
        self.docker
            .create_image(
                Some(CreateImageOptions {
                    from_image: &self.config.image_name,
                    ..Default::default()
                }),
                None,
                None,
            )
            .await?;

        // コンテナの作成
        let container = self.docker
            .create_container(
                Some(CreateContainerOptions { name: "" }),
                Config {
                    image: Some(&self.config.image_name),
                    cmd: Some(vec!["python", "-c", source_code]),
                    memory: Some(self.config.memory_limit_mb * 1024 * 1024),
                    ..Default::default()
                },
            )
            .await?;

        self.container_id = container.id;
        
        // コンテナの起動
        self.docker
            .start_container(&self.container_id, None::<StartContainerOptions<String>>)
            .await?;

        *self.state.lock().await = RunnerState::Running;
        Ok(())
    }

    pub async fn write(&self, input: &str) -> Result<(), Box<dyn std::error::Error>> {
        if *self.state.lock().await != RunnerState::Running {
            return Err("Container is not running".into());
        }

        let exec = self.docker
            .create_exec(
                &self.container_id,
                CreateExecOptions {
                    attach_stdin: Some(true),
                    attach_stdout: Some(true),
                    attach_stderr: Some(true),
                    cmd: Some(vec!["echo", input]),
                    ..Default::default()
                },
            )
            .await?;

        match timeout(
            Duration::from_secs(self.config.timeout_seconds),
            self.docker.start_exec(&exec.id, None),
        )
        .await
        {
            Ok(Ok(StartExecResults::Attached { mut output, .. })) => {
                while let Some(Ok(output)) = output.next().await {
                    match output {
                        OutputType::StdOut(bytes) => {
                            let mut stdout = self.stdout_buffer.lock().await;
                            stdout.push(String::from_utf8_lossy(&bytes).to_string());
                        }
                        OutputType::StdErr(bytes) => {
                            let mut stderr = self.stderr_buffer.lock().await;
                            stderr.push(String::from_utf8_lossy(&bytes).to_string());
                        }
                    }
                }
                Ok(())
            }
            Ok(Err(e)) => {
                *self.state.lock().await = RunnerState::Error;
                Err(e.into())
            }
            Err(_) => {
                *self.state.lock().await = RunnerState::Error;
                Err("Execution timed out".into())
            }
            _ => Err("Unexpected execution result".into()),
        }
    }

    pub async fn read(&self) -> Result<String, Box<dyn std::error::Error>> {
        let stdout = self.stdout_buffer.lock().await;
        Ok(stdout.last().cloned().unwrap_or_default())
    }

    pub async fn read_all(&self) -> Result<String, Box<dyn std::error::Error>> {
        let stdout = self.stdout_buffer.lock().await;
        Ok(stdout.join("\n"))
    }

    pub async fn read_error(&self) -> Result<String, Box<dyn std::error::Error>> {
        let stderr = self.stderr_buffer.lock().await;
        Ok(stderr.join("\n"))
    }

    pub async fn stop(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        self.docker.stop_container(&self.container_id, None).await?;
        self.docker.remove_container(&self.container_id, None).await?;
        *self.state.lock().await = RunnerState::Stop;
        Ok(())
    }
}

impl Drop for DockerRunner {
    fn drop(&mut self) {
        if !self.container_id.is_empty() {
            let docker = self.docker.clone();
            let container_id = self.container_id.clone();
            tokio::spawn(async move {
                let _ = docker.remove_container(&container_id, None).await;
            });
        }
    }
}