use bollard::exec::CreateExecOptions;
use bollard::container::{LogsOptions, LogOutput};
use futures::StreamExt;
use tokio::time::timeout;
use std::time::Duration;
use thiserror::Error;

use crate::docker::state::RunnerState;

#[derive(Error, Debug)]
pub enum IOError {
    #[error("Container not initialized for writing")]
    ContainerNotInitialized,
    #[error("Failed to write to container: {0}")]
    WriteError(String),
    #[error("Failed to read from container: {0}")]
    ReadError(String),
    #[error("Timeout error: {0}")]
    TimeoutError(String),
}

pub trait IOHandler {
    async fn write(&self, input: &str) -> Result<(), IOError>;
    async fn read(&self) -> Result<String, IOError>;
    async fn read_error(&self) -> Result<String, IOError>;
    async fn setup_io(&mut self) -> Result<(), IOError>;
}

impl IOHandler for DockerRunner {
    async fn write(&self, input: &str) -> Result<(), IOError> {
        println!("Writing to container: {}", input);
        let tx = self.stdin_tx.as_ref()
            .ok_or(IOError::ContainerNotInitialized)?;

        tx.send(input.to_string())
            .await
            .map_err(|e| IOError::WriteError(e.to_string()))?;
        
        println!("Successfully wrote to container");
        Ok(())
    }

    async fn read(&self) -> Result<String, IOError> {
        println!("Attempting to read from container");
        let stdout = self.stdout_buffer.lock().await;
        Ok(stdout.last()
            .cloned()
            .unwrap_or_default())
    }

    async fn read_error(&self) -> Result<String, IOError> {
        let stderr = self.stderr_buffer.lock().await;
        Ok(stderr.last()
            .cloned()
            .unwrap_or_default())
    }

    async fn setup_io(&mut self) -> Result<(), IOError> {
        println!("Setting up I/O for container: {}", self.container_id);
        let (tx, mut rx) = tokio::sync::mpsc::channel::<String>(32);
        self.stdin_tx = Some(tx);

        let container_id = self.container_id.clone();
        let docker = self.docker.clone();
        let stdout_buffer = self.stdout_buffer.clone();
        let stderr_buffer = self.stderr_buffer.clone();
        let state = self.state.clone();

        let timeout_seconds = self.config
            .get::<u64>("system.docker.timeout_seconds")
            .map_err(|e| IOError::TimeoutError(e.to_string()))?;
        
        let stdout_options = LogsOptions::<String> {
            follow: true,
            stdout: true,
            stderr: false,
            ..Default::default()
        };

        let stderr_options = LogsOptions::<String> {
            follow: true,
            stdout: false,
            stderr: true,
            ..Default::default()
        };

        let stdout_container_id = container_id.clone();
        let mut stdout_stream = docker.logs(&stdout_container_id, Some(stdout_options));
        tokio::spawn(async move {
            while let Some(Ok(output)) = stdout_stream.next().await {
                if let LogOutput::StdOut { message } = output {
                    let output = String::from_utf8_lossy(&message).to_string();
                    println!("Container stdout: {}", output);
                    stdout_buffer.lock().await.push(output);
                }
            }
            println!("Stdout stream ended for container {}", stdout_container_id);
        });

        let stderr_container_id = container_id.clone();
        let mut stderr_stream = docker.logs(&stderr_container_id, Some(stderr_options));
        tokio::spawn(async move {
            while let Some(Ok(output)) = stderr_stream.next().await {
                if let LogOutput::StdErr { message } = output {
                    let error = String::from_utf8_lossy(&message).to_string();
                    println!("Container stderr: {}", error);
                    stderr_buffer.lock().await.push(error);
                }
            }
            println!("Stderr stream ended for container {}", stderr_container_id);
        });

        let input_container_id = container_id.clone();
        let input_docker = docker.clone();
        tokio::spawn(async move {
            while let Some(input) = rx.recv().await {
                println!("Processing input: {}", input);
                match timeout(timeout_duration, async {
                    let exec = match input_docker
                        .create_exec(
                            &input_container_id,
                            CreateExecOptions {
                                attach_stdin: Some(true),
                                attach_stdout: Some(true),
                                attach_stderr: Some(true),
                                cmd: Some(vec!["sh".to_string(), "-c".to_string(), format!("printf '%s' '{}' > /proc/1/fd/0", input.replace("'", "'\"'\"'"))]),
                                ..Default::default()
                            },
                        )
                        .await {
                            Ok(exec) => exec,
                            Err(e) => {
                                println!("Failed to create exec: {:?}", e);
                                return;
                            }
                        };

                    if let Err(e) = input_docker.start_exec(&exec.id, None).await {
                        println!("Failed to start exec: {:?}", e);
                        return;
                    }
                })
                .await
                {
                    Ok(_) => println!("Successfully processed input"),
                    Err(_) => {
                        println!("Input processing timed out");
                        *state.lock().await = RunnerState::Error;
                    }
                }
            }
            println!("Input channel closed for container {}", input_container_id);
        });

        println!("I/O setup completed for container {}", self.container_id);
        Ok(())
    }
}

// ... existing helper functions and implementations ...